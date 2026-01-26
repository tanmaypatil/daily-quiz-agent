# Adding Swap Space on AWS Lightsail

## Why Swap is Needed

Lightsail instances with 512MB RAM can run out of memory during:
- `pip install` with large packages (anthropic, google-auth, etc.)
- Running the Flask app with Gunicorn
- Quiz generation with Claude API calls

Swap uses disk space as virtual memory, preventing crashes when RAM is exhausted.

---

## Quick Setup (Copy-Paste)

Run these commands in order:

```bash
# 1. Create 1GB swap file
sudo fallocate -l 1G /swapfile

# 2. Secure the file
sudo chmod 600 /swapfile

# 3. Set up swap space
sudo mkswap /swapfile

# 4. Enable swap
sudo swapon /swapfile

# 5. Make permanent (survives reboot)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 6. Verify it's working
free -h
```

---

## Expected Output

After running `free -h`, you should see:

```
              total        used        free      shared  buff/cache   available
Mem:          476Mi       150Mi        50Mi       1.0Mi       275Mi       200Mi
Swap:         1.0Gi          0B       1.0Gi
```

The `Swap: 1.0Gi` line confirms swap is active.

---

## Step-by-Step Explanation

### Step 1: Create Swap File

```bash
sudo fallocate -l 1G /swapfile
```

Creates a 1GB file at `/swapfile`. For very memory-intensive tasks, use `2G` instead.

### Step 2: Secure Permissions

```bash
sudo chmod 600 /swapfile
```

Only root can read/write the swap file. This prevents other users from accessing memory contents.

### Step 3: Format as Swap

```bash
sudo mkswap /swapfile
```

Formats the file for use as swap space.

### Step 4: Enable Swap

```bash
sudo swapon /swapfile
```

Activates the swap immediately.

### Step 5: Make Permanent

```bash
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Adds entry to `/etc/fstab` so swap is enabled automatically on reboot.

### Step 6: Verify

```bash
free -h
```

Shows current memory and swap usage.

---

## Tuning Swap Behavior (Optional)

### Swappiness

Controls how aggressively the system uses swap. Default is 60.

```bash
# Check current value
cat /proc/sys/vm/swappiness

# Set to 10 (use swap only when necessary)
sudo sysctl vm.swappiness=10

# Make permanent
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

Lower values (10-20) are better for servers - keeps more in RAM when possible.

---

## Troubleshooting

### "fallocate failed: Operation not supported"

Use `dd` instead:
```bash
sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
```

### Swap not showing after reboot

Check `/etc/fstab` has the entry:
```bash
cat /etc/fstab | grep swap
```

If missing, add it:
```bash
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Check swap usage

```bash
# Current usage
swapon --show

# Detailed memory info
cat /proc/meminfo | grep -i swap
```

---

## Removing Swap (If Needed)

```bash
# Disable swap
sudo swapoff /swapfile

# Remove from fstab
sudo sed -i '/swapfile/d' /etc/fstab

# Delete the file
sudo rm /swapfile
```

---

## Recommendations for CLAT Quiz App

| Instance RAM | Recommended Swap |
|--------------|------------------|
| 512MB        | 1GB (minimum)    |
| 1GB          | 1GB              |
| 2GB+         | Optional         |

For 512MB instances, swap is **required** for reliable operation.

---

## After Adding Swap

Continue with deployment:

```bash
cd /var/www/quiz
source venv/bin/activate
pip install -r requirements.txt
```

The install should now complete without memory issues.
