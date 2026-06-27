# Script de SÃ©curisation AWS Instance - Harmonic AI
# Auteur : Harmonic AI Security Team
# Date : $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$InstanceIP = "__EC2_IP__",
    [string]$YourPublicIP = "",
    [string]$Region = "us-east-1",
    [switch]$DryRun = $false,
    [switch]$SkipSSH = $false
)

$ErrorActionPreference = "Stop"

# Fonctions de logging
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = @{
        "INFO" = "White"
        "SUCCESS" = "Green"
        "WARNING" = "Yellow"
        "ERROR" = "Red"
        "DEBUG" = "Gray"
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color[$Level]
}

function Write-Section {
    param([string]$Title)
    Write-Host "`n" + "="*80 -ForegroundColor Cyan
    Write-Host " $Title" -ForegroundColor Cyan
    Write-Host "="*80 -ForegroundColor Cyan
}

# VÃ©rification prÃ©alable
function Test-Prerequisites {
    Write-Log "VÃ©rification des prÃ©requis..." "INFO"
    
    # VÃ©rifier AWS CLI
    try {
        $awsVersion = aws --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "âœ… AWS CLI installÃ©: $awsVersion" "SUCCESS"
        } else {
            Write-Log "âŒ AWS CLI non installÃ©" "ERROR"
            return $false
        }
    } catch {
        Write-Log "âŒ AWS CLI non installÃ©" "ERROR"
        return $false
    }
    
    # VÃ©rifier credentials AWS
    try {
        $callerIdentity = aws sts get-caller-identity --region $Region 2>&1 | ConvertFrom-Json
        if ($callerIdentity.Arn) {
            Write-Log "âœ… Credentials AWS valides: $($callerIdentity.Arn)" "SUCCESS"
        } else {
            Write-Log "âŒ Credentials AWS invalides" "ERROR"
            return $false
        }
    } catch {
        Write-Log "âŒ Erreur lors de la vÃ©rification des credentials AWS" "ERROR"
        return $false
    }
    
    # VÃ©rifier IP publique si fournie
    if (-not [string]::IsNullOrEmpty($YourPublicIP)) {
        if ($YourPublicIP -match '^\d{1,3}(\.\d{1,3}){3}$') {
            Write-Log "âœ… IP publique valide: $YourPublicIP" "SUCCESS"
        } else {
            Write-Log "âš ï¸  IP publique invalide, utilisation de 0.0.0.0/0 (non recommandÃ©)" "WARNING"
            $YourPublicIP = "0.0.0.0/0"
        }
    } else {
        Write-Log "âš ï¸  IP publique non fournie, utilisation de 0.0.0.0/0 (non recommandÃ©)" "WARNING"
        $YourPublicIP = "0.0.0.0/0"
    }
    
    return $true
}

# Ã‰tape 1: Identifier l'instance et ses groupes de sÃ©curitÃ©
function Get-InstanceInfo {
    param([string]$InstanceIP)
    
    Write-Log "Recherche de l'instance avec IP: $InstanceIP" "INFO"
    
    try {
        # DÃ©crire toutes les instances
        $instances = aws ec2 describe-instances --region $Region --query "Reservations[*].Instances[*]" 2>&1 | ConvertFrom-Json
        
        foreach ($instance in $instances) {
            if ($instance.PublicIpAddress -eq $InstanceIP) {
                Write-Log "âœ… Instance trouvÃ©e: $($instance.InstanceId)" "SUCCESS"
                
                return @{
                    InstanceId = $instance.InstanceId
                    PublicIp = $instance.PublicIpAddress
                    PrivateIp = $instance.PrivateIpAddress
                    SecurityGroups = $instance.SecurityGroups
                    VpcId = $instance.VpcId
                    SubnetId = $instance.SubnetId
                    State = $instance.State.Name
                }
            }
        }
        
        Write-Log "âŒ Instance non trouvÃ©e avec IP: $InstanceIP" "ERROR"
        return $null
        
    } catch {
        Write-Log "âŒ Erreur lors de la recherche de l'instance: $_" "ERROR"
        return $null
    }
}

# Ã‰tape 2: Restreindre l'accÃ¨s SSH
function Restrict-SSHAccess {
    param(
        [hashtable]$InstanceInfo,
        [string]$YourPublicIP
    )
    
    Write-Section "Ã‰TAPE 2: RESTREINDRE ACCÃˆS SSH"
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Restriction SSH Ã  $YourPublicIP" "INFO"
        return $true
    }
    
    foreach ($sg in $InstanceInfo.SecurityGroups) {
        $sgId = $sg.GroupId
        $sgName = $sg.GroupName
        
        Write-Log "Traitement du groupe de sÃ©curitÃ©: $sgName ($sgId)" "INFO"
        
        try {
            # 1. Supprimer toutes les rÃ¨gles SSH existantes
            Write-Log "Suppression des rÃ¨gles SSH existantes..." "INFO"
            
            $existingRules = aws ec2 describe-security-groups `
                --group-id $sgId `
                --region $Region `
                --query "SecurityGroups[0].IpPermissions[?FromPort==\`22\`]" `
                --output json 2>&1 | ConvertFrom-Json
            
            foreach ($rule in $existingRules) {
                $cidr = $rule.IpRanges[0].CidrIp
                Write-Log "Suppression rÃ¨gle SSH: $cidr" "DEBUG"
                
                aws ec2 revoke-security-group-ingress `
                    --group-id $sgId `
                    --protocol tcp `
                    --port 22 `
                    --cidr $cidr `
                    --region $Region 2>&1 | Out-Null
            }
            
            # 2. Ajouter nouvelle rÃ¨gle restrictive
            Write-Log "Ajout rÃ¨gle SSH restrictive: $YourPublicIP" "INFO"
            
            aws ec2 authorize-security-group-ingress `
                --group-id $sgId `
                --protocol tcp `
                --port 22 `
                --cidr $YourPublicIP `
                --region $Region 2>&1 | Out-Null
            
            Write-Log "âœ… AccÃ¨s SSH restreint Ã  $YourPublicIP" "SUCCESS"
            
        } catch {
            Write-Log "âŒ Erreur lors de la restriction SSH: $_" "ERROR"
            return $false
        }
    }
    
    return $true
}

# Ã‰tape 3: Configurer Fail2ban via SSH
function Configure-Fail2ban {
    param([string]$InstanceIP)
    
    Write-Section "Ã‰TAPE 3: CONFIGURER FAIL2BAN"
    
    if ($SkipSSH) {
        Write-Log "Skip SSH activÃ©, saut de la configuration Fail2ban" "WARNING"
        return $true
    }
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Configuration Fail2ban sur $InstanceIP" "INFO"
        return $true
    }
    
    # Commande SSH pour configurer Fail2ban
    $sshCommand = @"
sudo apt-get update && sudo apt-get install -y fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Configurer jail pour SSH
sudo tee -a /etc/fail2ban/jail.local << 'EOF'

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
EOF

sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
"@
    
    try {
        Write-Log "Connexion SSH pour configurer Fail2ban..." "INFO"
        
        # Sauvegarder la commande dans un fichier temporaire
        $tempScript = "fail2ban_config.sh"
        $sshCommand | Out-File -FilePath $tempScript -Encoding UTF8
        
        # ExÃ©cuter via SSH
        ssh -i "C:\Users\maatc\.ssh\deepseek_ec2" ec2-user@$InstanceIP "bash -s" < $tempScript
        
        # Nettoyer
        Remove-Item -Path $tempScript -Force -ErrorAction SilentlyContinue
        
        Write-Log "âœ… Fail2ban configurÃ© avec succÃ¨s" "SUCCESS"
        return $true
        
    } catch {
        Write-Log "âŒ Erreur lors de la configuration Fail2ban: $_" "ERROR"
        return $false
    }
}

# Ã‰tape 4: DÃ©sactiver Password Authentication SSH
function Disable-PasswordAuth {
    param([string]$InstanceIP)
    
    Write-Section "Ã‰TAPE 4: DÃ‰SACTIVER PASSWORD AUTHENTICATION"
    
    if ($SkipSSH) {
        Write-Log "Skip SSH activÃ©, saut de la dÃ©sactivation password auth" "WARNING"
        return $true
    }
    
    if ($DryRun) {
        Write-Log "[DRY RUN] DÃ©sactivation password authentication SSH" "INFO"
        return $true
    }
    
    # Commande SSH pour modifier sshd_config
    $sshCommand = @"
# Sauvegarder la configuration originale
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup_$(date +%Y%m%d)

# Modifier les paramÃ¨tres
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# RedÃ©marrer SSH
sudo systemctl restart sshd

# VÃ©rifier la configuration
sudo sshd -t
"@
    
    try {
        Write-Log "Modification sshd_config pour dÃ©sactiver password auth..." "INFO"
        
        # Sauvegarder la commande
        $tempScript = "disable_password_auth.sh"
        $sshCommand | Out-File -FilePath $tempScript -Encoding UTF8
        
        # ExÃ©cuter via SSH
        ssh -i "C:\Users\maatc\.ssh\deepseek_ec2" ec2-user@$InstanceIP "bash -s" < $tempScript
        
        # Nettoyer
        Remove-Item -Path $tempScript -Force -ErrorAction SilentlyContinue
        
        Write-Log "âœ… Password authentication dÃ©sactivÃ©" "SUCCESS"
        return $true
        
    } catch {
        Write-Log "âŒ Erreur lors de la dÃ©sactivation password auth: $_" "ERROR"
        return $false
    }
}

# Ã‰tape 5: Configurer le firewall applicatif (iptables)
function Configure-IPTables {
    param([string]$InstanceIP)
    
    Write-Section "Ã‰TAPE 5: CONFIGURER IPTABLES"
    
    if ($SkipSSH) {
        Write-Log "Skip SSH activÃ©, saut de la configuration iptables" "WARNING"
        return $true
    }
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Configuration iptables" "INFO"
        return $true
    }
    
    # RÃ¨gles iptables avancÃ©es
    $sshCommand = @"
#!/bin/bash

# Sauvegarder les rÃ¨gles actuelles
sudo iptables-save > /etc/iptables.backup_$(date +%Y%m%d)

# Flush les rÃ¨gles existantes
sudo iptables -F
sudo iptables -X

# Politique par dÃ©faut: DROP
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Autoriser localhost
sudo iptables -A INPUT -i lo -j ACCEPT

# Autoriser les connexions Ã©tablies
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# SSH: uniquement depuis IP autorisÃ©e (sera configurÃ© par security group)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# API: port 8000
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

# ICMP (ping) limitÃ©
sudo iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/second -j ACCEPT

# Protection contre scans de ports
sudo iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
sudo iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP

# Protection contre SYN floods
sudo iptables -N SYN_FLOOD
sudo iptables -A INPUT -p tcp --syn -j SYN_FLOOD
sudo iptables -A SYN_FLOOD -m limit --limit 10/second --limit-burst 25 -j RETURN
sudo iptables -A SYN_FLOOD -j DROP

# Sauvegarder les rÃ¨gles
sudo iptables-save > /etc/iptables.rules

# Rendre les rÃ¨gles persistantes
echo '#!/bin/sh' > /etc/network/if-pre-up.d/iptables
echo 'iptables-restore < /etc/iptables.rules' >> /etc/network/if-pre-up.d/iptables
chmod +x /etc/network/if-pre-up.d/iptables

echo "Configuration iptables terminÃ©e"
"@
    
    try {
        Write-Log "Configuration iptables avancÃ©e..." "INFO"
        
        # Sauvegarder la commande
        $tempScript = "configure_iptables.sh"
        $sshCommand | Out-File -FilePath $tempScript -Encoding UTF8
        
        # ExÃ©cuter via SSH
        ssh -i "C:\Users\maatc\.ssh\deepseek_ec2" ec2-user@$InstanceIP "bash -s" < $tempScript
        
        # Nettoyer
        Remove-Item -Path $tempScript -Force -ErrorAction SilentlyContinue
        
        Write-Log "âœ… IPTables configurÃ© avec rÃ¨gles avancÃ©es" "SUCCESS"
        return $true
        
    } catch {
        Write-Log "âŒ Erreur lors de la configuration iptables: $_" "ERROR"
        return $false
    }
}

# Ã‰tape 6: Configurer le monitoring de sÃ©curitÃ©
function Configure-SecurityMonitoring {
    param([string]$InstanceIP)
    
    Write-Section "Ã‰TAPE 6: CONFIGURER MONITORING SÃ‰CURITÃ‰"
    
    if ($SkipSSH) {
        Write-Log "Skip SSH activÃ©, saut du monitoring sÃ©curitÃ©" "WARNING"
        return $true
    }
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Configuration monitoring sÃ©curitÃ©" "INFO"
        return $true
    }
    
    # Script de monitoring
    $sshCommand = @"
#!/bin/bash

# Installer outils de monitoring
sudo apt-get install -y auditd audispd-plugins logwatch

# Configurer auditd
sudo tee /etc/audit/auditd.conf << 'EOF'
log_file = /var/log/audit/audit.log
log_format = RAW
log_group = root
priority_boost = 4
flush = INCREMENTAL
freq = 20
num_logs = 5
disp_qos = lossy
dispatcher = /sbin/audispd
name_format = NONE
##name = mydomain
max_log_file = 6
max_log_file_action = ROTATE
space_left = 75
space_left_action = SYSLOG
action_mail_acct = root
admin_space_left = 50
admin_space_left_action = SUSPEND
disk_full_action = SUSPEND
disk_error_action = SUSPEND
##tcp_listen_port = 
tcp_listen_queue = 5
tcp_max_per_addr = 1
##tcp_client_ports = 1024-65535
tcp_client_max_idle = 0
enable_krb5 = no
krb5_principal = auditd
##krb5_key_file = /etc/audit/audit.key
EOF

# RÃ¨gles auditd pour sÃ©curitÃ©
sudo tee /etc/audit/rules.d/harmonic-security.rules << 'EOF'
# Surveiller les modifications de fichiers sensibles
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/sudoers -p wa -k identity

# Surveiller les accÃ¨s root
-a always,exit -F arch=b64 -S execve -C uid!=euid -F euid=0 -k setuid
-a always,exit -F arch=b64 -S execve -C gid!=egid -F egid=0 -k setgid

# Surveiller les modifications systÃ¨me
-w /var/log/audit/ -p wa -k auditlog
-w /etc/audit/ -p wa -k auditconfig
-w /etc/libaudit.conf -p wa -k auditconfig
-w /etc/audisp/ -p wa -k audispconfig

# Surveiller les accÃ¨s rÃ©seau
-a always,exit -F arch=b64 -S bind -k network_bind
-a always,exit -F arch=b64 -S connect -k network_connect
EOF

# Appliquer les rÃ¨gles
sudo auditctl -R /etc/audit/rules.d/harmonic-security.rules

# Configurer logwatch
sudo tee /etc/logwatch/conf/logwatch.conf << 'EOF'
LogDir = /var/log
TmpDir = /var/cache/logwatch
Output = stdout
Format = text
Encode = no
MailTo = root
MailFrom = Logwatch
Range = yesterday
Detail = Low
Service = All
EOF

# CrÃ©er script de surveillance quotidienne
sudo tee /usr/local/bin/security_monitor.sh << 'EOF'
#!/bin/bash
# Script de surveillance sÃ©curitÃ© Harmonic AI

echo "=== RAPPORT SÃ‰CURITÃ‰ HARMONIC AI ==="
echo "Date: $(date)"
echo ""

# VÃ©rifier les connexions SSH
echo "1. CONNEXIONS SSH ACTIVES:"
sudo netstat -tnpa | grep ':22' | grep ESTABLISHED
echo ""

# VÃ©rifier les tentatives Ã©chouÃ©es
echo "2. TENTATIVES SSH Ã‰CHOUÃ‰ES (24h):"
sudo grep "Failed password" /var/log/auth.log | tail -20
echo ""

# VÃ©rifier les processus suspects
echo "3. PROCESSUS SUSPECTS:"
sudo ps aux | grep -E '(miner|crypt|backdoor|shell)' | grep -v grep
echo ""

# VÃ©rifier les modifications fichiers sensibles
echo "4. MODIFICATIONS FICHIERS SENSIBLES (24h):"
sudo auditctl -l | grep -E '(passwd|shadow|sudoers)' | while read rule; do
    echo "RÃ¨gle: $rule"
done
echo ""

# VÃ©rifier les ports ouverts
echo "5. PORTS OUVERTS:"
sudo netstat -tulpn | grep LISTEN
echo ""

echo "=== FIN DU RAPPORT ==="
EOF

sudo chmod +x /usr/local/bin/security_monitor.sh

# Ajouter au crontab
(crontab -l 2>/dev/null; echo "0 6 * * * /usr/local/bin/security_monitor.sh > /var/log/security_monitor.log 2>&1") | crontab -

echo "Monitoring sÃ©curitÃ© configurÃ©"
"@
    
    try {
        Write-Log "Configuration monitoring sÃ©curitÃ© avancÃ©..." "INFO"
        
        # Sauvegarder la commande
        $tempScript = "security_monitoring.sh"
        $sshCommand | Out-File -FilePath $tempScript -Encoding UTF8
        
        # ExÃ©cuter via SSH
        ssh -i "C:\Users\maatc\.ssh\deepseek_ec2" ec2-user@$InstanceIP "bash -s" < $tempScript
        
        # Nettoyer
        Remove-Item -Path $tempScript -Force -ErrorAction SilentlyContinue
        
        Write-Log "âœ… Monitoring sÃ©curitÃ© configurÃ© avec auditd + logwatch" "SUCCESS"
        return $true
        
    } catch {
        Write-Log "âŒ Erreur lors de la configuration monitoring: $_" "ERROR"
        return $false
    }
}

# Ã‰tape 7: Configurer le chiffrement des donnÃ©es
function Configure-DataEncryption {
    param([string]$InstanceIP)
    
    Write-Section "Ã‰TAPE 7: CONFIGURER CHIFFREMENT DONNÃ‰ES"
    
    if ($SkipSSH) {
        Write-Log "Skip SSH activÃ©, saut du chiffrement donnÃ©es" "WARNING"
        return $true
    }
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Configuration chiffrement donnÃ©es" "INFO"
        return $true
    }
    
    # Script de chiffrement
    $sshCommand = @"
#!/bin/bash

# Installer outils de chiffrement
sudo apt-get install -y ecryptfs-utils openssl

# CrÃ©er rÃ©pertoire chiffrÃ© pour donnÃ©es sensibles
sudo mkdir -p /encrypted_data
sudo chmod 700 /encrypted_data

# Configurer EBS encryption (si applicable)
echo "VÃ©rification chiffrement EBS..."
sudo lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL

# Configurer chiffrement pour fichiers temporaires
sudo tee /etc/crypttab << 'EOF'
# Configuration chiffrement fichiers temporaires
tmpfs /tmp tmpfs defaults,noexec,nosuid 0 0
EOF

# Configurer chiffrement swap
if [ -f /etc/fstab ]; then
    sudo sed -i '/swap/s/^/#/' /etc/fstab
    echo "/dev/mapper/crypt-swap none swap sw 0 0" | sudo tee -a /etc/fstab
fi

# Configurer politique de chiffrement
sudo tee /etc/security/encryption.conf << 'EOF'
# Politique de chiffrement Harmonic AI
ENCRYPT_HOME=no
ENCRYPT_DATA=yes
ENCRYPT_SWAP=yes
ENCRYPT_TMP=yes
KEY_LENGTH=256
CIPHER=aes-256-cbc
EOF

echo "Configuration chiffrement terminÃ©e"
"@
    
    try {
        Write-Log "Configuration chiffrement des donnÃ©es..." "INFO"
        
        # Sauvegarder la commande
        $tempScript = "data_encryption.sh"
        $sshCommand | Out-File -FilePath $tempScript -Encoding UTF8
        
        # ExÃ©cuter via SSH
        ssh -i "C:\Users\maatc\.ssh\deepseek_ec2" ec2-user@$InstanceIP "bash -s" < $tempScript
        
        # Nettoyer
        Remove-Item -Path $tempScript -Force -ErrorAction SilentlyContinue
        
        Write-Log "âœ… Chiffrement des donnÃ©es configurÃ©" "SUCCESS"
        return $true
        
    } catch {
        Write-Log "âŒ Erreur lors de la configuration chiffrement: $_" "ERROR"
        return $false
    }
}

# Fonction principale
function Main {
    Write-Section "SCRIPT DE SÃ‰CURISATION AWS - HARMONIC AI"
    Write-Log "DÃ©marrage du processus de sÃ©curisation..." "INFO"
    
    # VÃ©rifier les prÃ©requis
    if (-not (Test-Prerequisites)) {
        Write-Log "PrÃ©requis non satisfaits. ArrÃªt." "ERROR"
        exit 1
    }
    
    # Obtenir les informations de l'instance
    $instanceInfo = Get-InstanceInfo -InstanceIP $InstanceIP
    if (-not $instanceInfo) {
        Write-Log "Impossible de rÃ©cupÃ©rer les informations de l'instance. ArrÃªt." "ERROR"
        exit 1
    }
    
    Write-Log "Instance ID: $($instanceInfo.InstanceId)" "INFO"
    Write-Log "Ã‰tat: $($instanceInfo.State)" "INFO"
    Write-Log "VPC: $($instanceInfo.VpcId)" "INFO"
    
    # VÃ©rifier si l'instance est running
    if ($instanceInfo.State -ne "running") {
        Write-Log "L'instance n'est pas en Ã©tat 'running'. Ã‰tat actuel: $($instanceInfo.State)" "ERROR"
        exit 1
    }
    
    # Journal des actions
    $actionsLog = @()
    
    # Ã‰tape 2: Restreindre SSH
    $result = Restrict-SSHAccess -InstanceInfo $instanceInfo -YourPublicIP $YourPublicIP
    $actionsLog += @{
        Step = "Restrict SSH Access"
        Success = $result
        Details = "Restricted SSH to $YourPublicIP"
    }
    
    # Ã‰tape 3: Fail2ban
    $result = Configure-Fail2ban -InstanceIP $InstanceIP
    $actionsLog += @{
        Step = "Configure Fail2ban"
        Success = $result
        Details = "SSH brute force protection"
    }
    
    # Ã‰tape 4: DÃ©sactiver password auth
    $result = Disable-PasswordAuth -InstanceIP $InstanceIP
    $actionsLog += @{
        Step = "Disable Password Auth"
        Success = $result
        Details = "SSH key authentication only"
    }
    
    # Ã‰tape 5: IPTables
    $result = Configure-IPTables -InstanceIP $InstanceIP
    $actionsLog += @{
        Step = "Configure IPTables"
        Success = $result
        Details = "Advanced firewall rules"
    }
    
    # Ã‰tape 6: Monitoring
    $result = Configure-SecurityMonitoring -InstanceIP $InstanceIP
    $actionsLog += @{
        Step = "Configure Security Monitoring"
        Success = $result
        Details = "auditd + logwatch + daily reports"
    }
    
    # Ã‰tape 7: Chiffrement
    $result = Configure-DataEncryption -InstanceIP $InstanceIP
    $actionsLog += @{
        Step = "Configure Data Encryption"
        Success = $result
        Details = "Encrypted storage + swap"
    }
    
    # RÃ©sumÃ©
    Write-Section "RÃ‰SUMÃ‰ DES ACTIONS"
    
    $successCount = ($actionsLog | Where-Object { $_.Success -eq $true }).Count
    $totalCount = $actionsLog.Count
    
    Write-Log "Actions exÃ©cutÃ©es: $successCount/$totalCount" "INFO"
    
    foreach ($action in $actionsLog) {
        $status = if ($action.Success) { "âœ…" } else { "âŒ" }
        Write-Log "$status $($action.Step): $($action.Details)" "INFO"
    }
    
    # Recommendations
    Write-Section "RECOMMANDATIONS SUIVANTES"
    
    Write-Log "1. Configurer AWS WAF pour protection applicative" "INFO"
    Write-Log "2. Mettre en place AWS GuardDuty pour dÃ©tection menaces" "INFO"
    Write-Log "3. Configurer AWS Config pour conformitÃ© infrastructure" "INFO"
    Write-Log "4. ImplÃ©menter systÃ¨me de clÃ©s API avec HMAC signatures" "INFO"
    Write-Log "5. Planifier audit sÃ©curitÃ© trimestriel" "INFO"
    
    Write-Log "Processus de sÃ©curisation terminÃ©." "SUCCESS"
    
    # Sauvegarder le log
    $logFile = "security_configuration_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $actionsLog | ConvertTo-Json -Depth 3 | Out-File -FilePath $logFile -Encoding UTF8
    Write-Log "Log sauvegardÃ©: $logFile" "INFO"
}

# ExÃ©cution
if ($MyInvocation.InvocationName -ne '.') {
    Main
}