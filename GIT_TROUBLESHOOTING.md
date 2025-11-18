# Git Pull/Push Troubleshooting Guide

## Error: "Could not read from remote repository"

This error typically occurs due to SSH authentication or network connectivity issues.

## Solution 1: Test SSH Connection to GitHub

On your server, test if SSH connection to GitHub works:

```bash
ssh -T git@github.com
```

**Expected output if working:**
```
Hi pouyakhn! You've successfully authenticated, but GitHub does not provide shell access.
```

**If you get "Permission denied" or connection errors**, proceed to Solution 2.

## Solution 2: Set Up SSH Key on Server

If you don't have an SSH key set up on your server:

1. **Generate SSH key** (if you don't have one):
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter to accept default location
   # Optionally set a passphrase
   ```

2. **Display your public key**:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

3. **Add SSH key to GitHub**:
   - Copy the output from step 2
   - Go to GitHub → Settings → SSH and GPG keys
   - Click "New SSH key"
   - Paste your key and save

4. **Test connection again**:
   ```bash
   ssh -T git@github.com
   ```

## Solution 3: Use HTTPS Instead of SSH

If SSH continues to fail, you can switch to HTTPS:

1. **Change remote URL to HTTPS**:
   ```bash
   git remote set-url origin https://github.com/pouyakhn/AITrendTracker.git
   ```

2. **Pull using HTTPS**:
   ```bash
   git pull origin main
   ```

   You'll be prompted for GitHub username and password (or personal access token).

3. **For password-less HTTPS** (using personal access token):
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `repo` permissions
   - Use token as password when prompted

## Solution 4: Check Network Connectivity

Test if you can reach GitHub:

```bash
# Test GitHub connectivity
ping github.com

# Test SSH port
nc -zv github.com 22
```

If these fail, check your server's firewall or network configuration.

## Solution 5: Verify Remote Configuration

Check your current remote configuration:

```bash
git remote -v
```

Should show:
```
origin  git@github.com:pouyakhn/AITrendTracker.git (fetch)
origin  git@github.com:pouyakhn/AITrendTracker.git (push)
```

If it shows a different URL, update it:
```bash
git remote set-url origin git@github.com:pouyakhn/AITrendTracker.git
```

## Quick Fix: Use HTTPS (Easiest)

If you want a quick solution, switch to HTTPS:

```bash
cd ~/Secondment
git remote set-url origin https://github.com/pouyakhn/AITrendTracker.git
git pull origin main
```

Then enter your GitHub username and password (or personal access token) when prompted.

## After Fixing

Once authentication is working, you should be able to pull:

```bash
git pull origin main
```

