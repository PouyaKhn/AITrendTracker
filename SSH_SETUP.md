# SSH Setup for GitHub on Server

Follow these steps to set up SSH authentication for GitHub on your server.

## Step 1: Cancel Any Stuck Commands

If you have a stuck `git pull` command, cancel it:
```bash
# Press Ctrl+C
```

## Step 2: Generate SSH Key

Generate a new SSH key on your server:

```bash
ssh-keygen -t ed25519 -C "server@ai-center.dk"
```

**When prompted:**
- **File location**: Press Enter to accept default (`~/.ssh/id_ed25519`)
- **Passphrase**: Press Enter for no passphrase (or set one if you prefer)

## Step 3: Display Your Public Key

Display the public key that you'll add to GitHub:

```bash
cat ~/.ssh/id_ed25519.pub
```

**Copy the entire output** - it should look like:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... server@ai-center.dk
```

## Step 4: Add SSH Key to GitHub

1. Go to: https://github.com/settings/keys
2. Click **"New SSH key"** button
3. **Title**: Enter a descriptive name (e.g., "AI Center Server")
4. **Key**: Paste the entire public key you copied in Step 3
5. Click **"Add SSH key"**

## Step 5: Test SSH Connection

Test if SSH authentication works:

```bash
ssh -T git@github.com
```

**Expected output:**
```
Hi pouyakhn! You've successfully authenticated, but GitHub does not provide shell access.
```

If you see this, SSH is working correctly!

## Step 6: Switch Git Remote to SSH

Change your git remote URL to use SSH:

```bash
cd ~/Secondment
git remote set-url origin git@github.com:pouyakhn/AITrendTracker.git
```

Verify the change:
```bash
git remote -v
```

Should show:
```
origin  git@github.com:pouyakhn/AITrendTracker.git (fetch)
origin  git@github.com:pouyakhn/AITrendTracker.git (push)
```

## Step 7: Pull from GitHub

Now you can pull without authentication prompts:

```bash
git pull origin main
```

## Troubleshooting

### If SSH test fails with "Permission denied"

1. **Check if SSH agent is running:**
   ```bash
   eval "$(ssh-agent -s)"
   ssh-add ~/.ssh/id_ed25519
   ```

2. **Verify key permissions:**
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/id_ed25519
   chmod 644 ~/.ssh/id_ed25519.pub
   ```

3. **Test connection with verbose output:**
   ```bash
   ssh -vT git@github.com
   ```
   This will show detailed connection information.

### If you get "Host key verification failed"

Remove old GitHub host key and try again:
```bash
ssh-keygen -R github.com
ssh -T git@github.com
# Type "yes" when asked to add the new host key
```

## Success!

Once SSH is set up, you can use git commands normally:
- `git pull origin main`
- `git push origin main`
- No password prompts needed!

