#!/usr/bin/env python3
"""
Neo4j Installation Script

Downloads and installs Neo4j Community Edition for ARM64 macOS.
Replaces obsolete embedded JAR approach with modern server-based solution.
Configures Neo4j with optimized settings for AI server workload.
"""

import os
import sys
import subprocess
import requests
import tarfile
import shutil
from pathlib import Path
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jInstaller:
    """Neo4j Community Edition installer for ARM64 macOS."""
    
    def __init__(self):
        self.version = "5.23.0"  # Latest stable version
        self.neo4j_url = f"https://dist.neo4j.org/neo4j-community-{self.version}-unix.tar.gz"
        self.install_dir = "/Users/server/Code/AI-projects/AI-server/services/storage/neo4j"
        self.neo4j_home = f"{self.install_dir}/neo4j-community-{self.version}"
        self.data_dir = f"{self.install_dir}/data"
        
    def check_java_installation(self) -> bool:
        """Check if Java 17+ is installed (required for Neo4j)."""
        try:
            result = subprocess.run(
                ["java", "-version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # Parse Java version from output
            version_line = result.stderr.split('\n')[0]
            if "17." in version_line or "21." in version_line or '"23.' in version_line:
                logger.info(f"Java found: {version_line.strip()}")
                return True
            else:
                logger.warning(f"Java version may be incompatible: {version_line.strip()}")
                return False
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Java not found. Please install Java 17+ for Neo4j")
            return False
    
    def install_java_if_needed(self) -> bool:
        """Install Java via Homebrew if not present."""
        # Check if Java 21 is available in PATH
        java_21_path = "/opt/homebrew/opt/openjdk@21/bin/java"
        if os.path.exists(java_21_path):
            # Set JAVA_HOME environment variable
            os.environ["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@21"
            os.environ["PATH"] = f"/opt/homebrew/opt/openjdk@21/bin:{os.environ.get('PATH', '')}"
            logger.info("Using Java 21 from Homebrew")
            return True
        
        if self.check_java_installation():
            return True
            
        logger.info("Installing Java 21 via Homebrew...")
        try:
            subprocess.run(["brew", "install", "openjdk@21"], check=True)
            
            # Set environment variables for Java 21
            os.environ["JAVA_HOME"] = "/opt/homebrew/opt/openjdk@21"
            os.environ["PATH"] = f"/opt/homebrew/opt/openjdk@21/bin:{os.environ.get('PATH', '')}"
            
            logger.info("Java 21 installed successfully (using Homebrew path)")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Java: {e}")
            return False
    
    def download_neo4j(self) -> bool:
        """Download Neo4j Community Edition."""
        logger.info(f"Downloading Neo4j {self.version}...")
        
        try:
            response = requests.get(self.neo4j_url, stream=True)
            response.raise_for_status()
            
            download_path = f"{self.install_dir}/neo4j-community-{self.version}-unix.tar.gz"
            os.makedirs(self.install_dir, exist_ok=True)
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Neo4j downloaded to: {download_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download Neo4j: {e}")
            return False
    
    def extract_neo4j(self) -> bool:
        """Extract Neo4j archive."""
        logger.info("Extracting Neo4j archive...")
        
        try:
            archive_path = f"{self.install_dir}/neo4j-community-{self.version}-unix.tar.gz"
            
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(self.install_dir)
            
            # Remove archive after extraction
            os.remove(archive_path)
            
            logger.info(f"Neo4j extracted to: {self.neo4j_home}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract Neo4j: {e}")
            return False
    
    def configure_neo4j(self) -> bool:
        """Configure Neo4j with optimized settings."""
        logger.info("Configuring Neo4j...")
        
        try:
            # Create configuration
            config_path = f"{self.neo4j_home}/conf/neo4j.conf"
            
            config_content = f"""# Neo4j Configuration for AI Server
# Optimized for ARM64 macOS with memory management

# Server configuration
server.default_listen_address=localhost
server.bolt.listen_address=localhost:7687
server.http.listen_address=localhost:7474
server.https.enabled=false

# Memory configuration (15% heap + 10% page cache of total RAM)
server.memory.heap.initial_size=19g
server.memory.heap.max_size=19g
server.memory.pagecache.size=13g

# JVM optimizations for ARM64
server.jvm.additional=-XX:+UseG1GC
server.jvm.additional=-XX:+UnlockExperimentalVMOptions
server.jvm.additional=-XX:+UseTransparentHugePages
server.jvm.additional=-Dfile.encoding=UTF-8

# Data directories
server.directories.data={self.data_dir}
server.directories.logs={self.data_dir}/logs
server.directories.transaction.logs.root={self.data_dir}/transactions

# Database tuning
db.checkpoint.interval.time=30m
db.checkpoint.interval.tx=100000
db.recovery.fail_on_missing_files=false

# Security
dbms.security.auth_enabled=true

# Logging
dbms.logs.gc.enabled=true
dbms.logs.debug.level=INFO

# Performance
db.tx_log.rotation.retention_policy=7 days 1G
"""
            
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            # Create data directories
            os.makedirs(f"{self.data_dir}/databases", exist_ok=True)
            os.makedirs(f"{self.data_dir}/transactions", exist_ok=True)
            os.makedirs(f"{self.data_dir}/logs", exist_ok=True)
            
            # Make Neo4j scripts executable
            bin_dir = f"{self.neo4j_home}/bin"
            for script in ["neo4j", "neo4j-admin", "cypher-shell"]:
                script_path = f"{bin_dir}/{script}"
                if os.path.exists(script_path):
                    os.chmod(script_path, 0o755)
            
            logger.info("Neo4j configuration completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure Neo4j: {e}")
            return False
    
    def install(self) -> bool:
        """Install Neo4j with all dependencies."""
        logger.info("Starting Neo4j installation process...")
        
        # Check and install Java
        if not self.install_java_if_needed():
            logger.error("Java installation failed - cannot continue")
            return False
        
        # Download Neo4j
        if not self.download_neo4j():
            return False
        
        # Extract Neo4j
        if not self.extract_neo4j():
            return False
        
        # Configure Neo4j
        if not self.configure_neo4j():
            return False
        
        logger.info("Neo4j installation completed successfully!")
        logger.info(f"Neo4j Home: {self.neo4j_home}")
        logger.info(f"Data Directory: {self.data_dir}")
        
        return True
    
    def get_start_command(self) -> str:
        """Get command to start Neo4j server."""
        return f"{self.neo4j_home}/bin/neo4j start"
    
    def get_stop_command(self) -> str:
        """Get command to stop Neo4j server."""
        return f"{self.neo4j_home}/bin/neo4j stop"


if __name__ == "__main__":
    installer = Neo4jInstaller()
    
    if installer.install():
        print("\n" + "="*60)
        print("NEO4J INSTALLATION SUCCESSFUL")
        print("="*60)
        print(f"Neo4j Home: {installer.neo4j_home}")
        print(f"Data Directory: {installer.data_dir}")
        print(f"Start command: {installer.get_start_command()}")
        print(f"Stop command: {installer.get_stop_command()}")
        print("\nNext steps:")
        print("1. Start Neo4j server")
        print("2. Set initial password")
        print("3. Test connection")
        print("="*60)
    else:
        print("Neo4j installation failed!")
        sys.exit(1)