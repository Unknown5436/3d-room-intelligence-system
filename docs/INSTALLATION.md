# Installation Guide

Complete guide for installing the 3D Room Intelligence System.

## Prerequisites

- Python 3.11+ (required for Open3D support)
- PostgreSQL 12+ with PostGIS extension
- 4GB+ RAM
- Linux/macOS/Windows

## Quick Installation

If you already have Python 3.11:

```bash
# Create virtual environment
python3.11 -m venv venv311

# Activate
source venv311/bin/activate  # Linux/macOS
# OR
venv311\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Detailed Installation

### Step 1: Install Python 3.11

**Why Python 3.11?** Open3D doesn't have wheels for Python 3.13+ yet.

#### Option A: Debian/Ubuntu (Recommended)

```bash
# Add Debian testing repository
echo "deb http://deb.debian.org/debian testing main" | sudo tee /etc/apt/sources.list.d/python311.list

# Pin to lower priority
sudo mkdir -p /etc/apt/preferences.d
sudo bash -c 'cat > /etc/apt/preferences.d/python311 << PREF
Package: *
Pin: release a=testing
Pin-Priority: 100
PREF'

# Install
sudo apt-get update
sudo apt-get install -y -t testing python3.11 python3.11-venv python3.11-dev python3.11-distutils

# Verify
python3.11 --version
```

#### Option B: Using pyenv (User-space, no sudo after initial setup)

```bash
# Install dependencies
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl libffi-dev liblzma-dev

# Install pyenv
curl https://pyenv.run | bash

# Add to shell profile (~/.bashrc or ~/.zshrc)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Reload shell
source ~/.bashrc

# Install Python 3.11
pyenv install 3.11.9
pyenv local 3.11.9
```

#### Option C: Using Conda

```bash
conda create -n room_intel python=3.11 -y
conda activate room_intel
```

#### Option D: Docker (Easiest)

```bash
docker build -f Dockerfile.dev -t room-intel .
docker run -it --rm -p 8000:8000 -v "$PWD:/app" room-intel
```

### Step 2: Create Virtual Environment

```bash
python3.11 -m venv venv311
source venv311/bin/activate  # Linux/macOS
# OR use virtualenv if python3.11-venv isn't available:
# virtualenv -p python3.11 venv311
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

This will install:
- **Open3D 0.19.0** - Point cloud processing
- **FastAPI 0.104.0** - Web framework
- **NumPy, SciPy** - Numerical computing
- **PostgreSQL drivers** - Database connectivity
- All other required packages

### Step 4: Verify Installation

```bash
python -c "import open3d; print(f'Open3D {open3d.__version__}')"
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
```

## Database Setup

### PostgreSQL with PostGIS

#### Option A: Docker (Recommended)

```bash
docker run -d \
  --name postgres-postgis \
  -e POSTGRES_USER=room_intel \
  -e POSTGRES_PASSWORD=secure_password \
  -e POSTGRES_DB=room_intelligence \
  -p 5432:5432 \
  postgis/postgis:15-3.3

# Wait for startup, then initialize
sleep 5
docker exec -i postgres-postgis psql -U room_intel -d room_intelligence < init.sql
```

#### Option B: Local PostgreSQL

```bash
# Install PostgreSQL and PostGIS
sudo apt-get install postgresql postgis postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE room_intelligence;
\c room_intelligence
CREATE EXTENSION postgis;
CREATE EXTENSION pointcloud;
\q

# Initialize schema
psql -U postgres -d room_intelligence -f init.sql
```

### Configure Connection

Create `.env` file:

```bash
DATABASE_URL=postgresql://room_intel:secure_password@localhost:5432/room_intelligence
```

## Troubleshooting

### Open3D Installation Issues

**Problem**: `No matching distribution found for open3d`

**Solution**: Use Python 3.11 (see Step 1 above). Open3D doesn't support Python 3.13+ yet.

### Database Connection Issues

**Problem**: Connection refused or authentication failed

**Solutions**:
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify connection string in `.env`
- Check firewall settings
- Ensure PostGIS extension is installed: `psql -d room_intelligence -c "SELECT PostGIS_Version();"`

### Virtual Environment Issues

**Problem**: `ensurepip is not available`

**Solution**: Install `python3.11-venv` package, or use `virtualenv` instead:

```bash
pip install virtualenv
virtualenv -p python3.11 venv311
```

## Next Steps

After installation, see:
- **[QUICK_START.md](QUICK_START.md)** - Get started with processing PLY files
- **[TESTING.md](TESTING.md)** - Testing guide

