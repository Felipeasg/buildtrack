# Deploying to Oracle Cloud Always Free (SSH push-deploy)

This project deploys via **GitHub Actions → SSH → `docker compose`** on a single
VPS. On every push to `main`, CI runs the tests, builds the images, and (if both
pass) SSHes into the VPS to pull the latest code and restart the stack.

- Pipeline: [`.github/workflows/deploy.yml`](../.github/workflows/deploy.yml)
- Production stack: [`docker-compose.prod.yml`](../docker-compose.prod.yml)

Only the **frontend** is exposed (port 80); it reverse-proxies `/api/` to the
backend internally, and Postgres is never published.

---

## 1. Create the Always Free instance

1. In the Oracle Cloud console: **Compute → Instances → Create instance**.
2. Image/shape: **Canonical Ubuntu 22.04**, shape **VM.Standard.A1.Flex**
   (Ampere ARM — Always Free allows up to 4 OCPU / 24 GB; 1 OCPU / 6 GB is
   plenty here). Add your SSH public key for the `ubuntu` user.
3. **Open port 80** (and 443 if you add HTTPS):
   - **VCN security list:** add an ingress rule, source `0.0.0.0/0`, TCP `80`.
   - **On the instance**, Oracle Ubuntu images block ports by default:
     ```bash
     sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
     sudo netfilter-persistent save
     ```

## 2. Install Docker on the VPS

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 git
sudo usermod -aG docker ubuntu      # log out/in afterwards so `docker` works without sudo
```

## 3. Get the code onto the VPS

```bash
sudo mkdir -p /opt/buildtrack && sudo chown ubuntu:ubuntu /opt/buildtrack
git clone https://github.com/<you>/buildtrack.git /opt/buildtrack
```

- **Public repo:** the HTTPS clone above just works.
- **Private repo:** create a read-only **deploy key** instead:
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/buildtrack_deploy -N ""
  # Add ~/.ssh/buildtrack_deploy.pub to GitHub → repo → Settings → Deploy keys (read-only)
  # Then clone via SSH:
  GIT_SSH_COMMAND='ssh -i ~/.ssh/buildtrack_deploy' \
    git clone git@github.com:<you>/buildtrack.git /opt/buildtrack
  ```

## 4. Create the production `.env`

`docker-compose.prod.yml` **requires** `SECRET_KEY` and will refuse to start
without it. Create `/opt/buildtrack/.env` (it is gitignored):

```bash
cd /opt/buildtrack
cat > .env <<EOF
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)
EOF
```

## 5. First manual deploy (sanity check)

```bash
cd /opt/buildtrack
docker compose -f docker-compose.prod.yml up -d --build
```

Visit `http://<vps-public-ip>/` — you should see the login page. Register an
account and confirm milestones/CSV import work.

## 6. Create the SSH deploy user for GitHub Actions

Generate a dedicated key pair **on your laptop** for the pipeline:

```bash
ssh-keygen -t ed25519 -f buildtrack_ci -N ""
# Install the PUBLIC key on the VPS:
ssh-copy-id -i buildtrack_ci.pub ubuntu@<vps-public-ip>
```

## 7. Add GitHub repository secrets

**Repo → Settings → Secrets and variables → Actions → New repository secret:**

| Secret     | Value                                                        |
| ---------- | ------------------------------------------------------------ |
| `SSH_HOST` | VPS public IP (or domain)                                    |
| `SSH_USER` | `ubuntu`                                                     |
| `SSH_KEY`  | Contents of the **private** key `buildtrack_ci` (entire file) |

`SECRET_KEY`/`POSTGRES_PASSWORD` live in the VPS `.env` — they are **not** needed
as GitHub secrets, because the build and run both happen on the VPS.

## 8. Ship it

Push to `main`:

```bash
git push origin main
```

Watch **Actions** in GitHub: `test` → `build` → `deploy`. The deploy job runs:

```bash
cd /opt/buildtrack
git fetch --all && git reset --hard origin/main
docker compose -f docker-compose.prod.yml up -d --build
docker image prune -f
```

---

## Notes & next steps

- **Branch name:** the pipeline targets `main`. If your repo uses `master`,
  either rename (`git branch -m master main`) or edit the `branches:` and
  `origin/main` references in `deploy.yml`.
- **Private repo + `git reset`:** the deploy step needs the VPS to be able to
  `git fetch`. With a public repo or the deploy key from step 3, this works as-is.
- **HTTPS:** for a real domain, put **Caddy** or **Traefik** in front of the
  frontend (automatic Let's Encrypt) and open port 443. Ask and I can add it.
- **First deploy must be manual** (step 5) so the VPS clone and `.env` exist;
  after that, every push to `main` redeploys automatically.
- **Builds run on the VPS** (ARM). All base images used here are multi-arch, so
  ARM builds work without changes.

---

## Other deployment patterns (for the future)

This project currently uses **Pattern 1 (SSH push-deploy)**, chosen for an
Oracle Cloud Always Free VM that is powerful enough to build images itself.
If the hosting situation changes (a weaker/free-tier box, a public repo, or a
desire for cleaner rollbacks), these are the alternatives worth revisiting:

| Pattern | How it works | Pros | Cons |
|---|---|---|---|
| **1. SSH push-deploy** (current) | Action SSHes in, runs `git pull && docker compose up -d --build` | Simplest mental model; no extra services on VPS; nothing extra to secure | VPS builds images (CPU/RAM heavy — matters on tiny free tiers); SSH key stored as GitHub secret |
| **2. Self-hosted runner on the VPS** | Install GitHub's runner on the VPS; the deploy job runs *locally* on the box | No inbound SSH from GitHub; build/deploy in one place; easy access to local docker | A long-lived runner process; **security risk if repo is public** (untrusted PRs could run code) — use only on private repos |
| **3. Registry + pull (GHCR + Watchtower)** | Actions build images, push to **GitHub Container Registry** (free); [Watchtower](https://containrrr.dev/watchtower/) on the VPS auto-pulls new images | VPS never builds (great for weak free VMs); clean rollbacks via tags; no inbound access needed | Two moving parts; need to push images and switch compose to `image:` instead of `build:` |
| **4. Webhook listener** | A tiny webhook service on the VPS triggers `git pull` + compose on push | Decoupled; no SSH secret in CI | One more service to run/secure; least common |

**When to switch:**

- Moving to a small/constrained VM (e.g. GCP `e2-micro` ~1 GB) or making the
  repo public → **Pattern 3**, so the box never builds and never accepts
  inbound CI connections.
- Want builds + deploy to happen entirely on the box without an SSH key in
  GitHub, and the repo stays private → **Pattern 2**.
