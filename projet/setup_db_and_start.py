#!/usr/bin/env python3
"""Setup PostgreSQL database and start the FastAPI backend."""
import subprocess, os, sys

PG_BIN = r"C:\Program Files\PostgreSQL\17\bin"
DB_NAME = "harmonic_saas"
DB_USER = "harmonic"
DB_PASS = "harmonic123"

def run_psql(sql, user="postgres"):
    """Run a SQL command via psql with env variable for password."""
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASS
    cmd = [os.path.join(PG_BIN, "psql.exe"), "-U", user, "-c", sql]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return result.returncode, result.stdout, result.stderr

def main():
    # 1. Check if database exists
    rc, out, err = run_psql(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'", "postgres")
    print(f"Check DB: rc={rc}")
    if rc != 0:
        # Try with postgres user and empty/known password
        env = os.environ.copy()
        env["PGPASSWORD"] = "postgres"
        cmd = [os.path.join(PG_BIN, "psql.exe"), "-U", "postgres", "-c", f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}';"]
        rc, out = subprocess.run(cmd, capture_output=True, text=True, env=env).returncode, subprocess.run(cmd, capture_output=True, text=True, env=env).stdout
        print(f"Check DB (postgres): {rc}")

    if "1" in (out or ""):
        print(f"✅ Database '{DB_NAME}' already exists")
    else:
        print(f"Creating database '{DB_NAME}'...")
        # Try to create user and database
        env = os.environ.copy()
        env["PGPASSWORD"] = "postgres"
        cmds = [
            f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASS}';",
            f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};",
            f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};"
        ]
        for sql in cmds:
            cmd = [os.path.join(PG_BIN, "psql.exe"), "-U", "postgres", "-c", sql]
            r = subprocess.run(cmd, capture_output=True, text=True, env=env)
            if r.returncode != 0 and "already exists" not in (r.stderr or ""):
                print(f"  → {r.stderr}")
        print(f"✅ Database '{DB_NAME}' created")

    # 2. Write .env file for the backend if not exists
    env_path = os.path.join("lm_arena_package", "config", ".env")
    if not os.path.exists(env_path):
        os.makedirs(os.path.dirname(env_path), exist_ok=True)
        with open(env_path, "w") as f:
            f.write(f"DATABASE_URL=postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}\n")
            f.write(f"JWT_SECRET_KEY=dev-secret-key-change-in-production-1234567890\n")
            f.write("API_V1_STR=/api/v1\n")
            f.write("BACKEND_CORS_ORIGINS=['http://localhost:8080','http://localhost:3000']\n")
            f.write("AUDIO_SERVICE_URL=http://localhost:9017\n")
            f.write("VIDEO_SERVICE_URL=http://localhost:9018\n")
            f.write("LM_ARENA_SERVICE_URL=http://localhost:8000\n")
            f.write("DEEPSEEK_API_KEY=dev-key\n")
        print(f"✅ .env file created at {env_path}")
    else:
        print(f"✅ .env file already exists at {env_path}")

    # 3. Also copy .env to harmonic_saas if needed
    saas_env = os.path.join("harmonic_saas", ".env")
    if not os.path.exists(saas_env):
        with open(saas_env, "w") as f:
            f.write(f"DATABASE_URL=postgresql://{DB_USER}:{DB_PASS}@localhost:5432/{DB_NAME}\n")
            f.write("JWT_SECRET_KEY=dev-secret-key-change-in-production-1234567890\n")
            f.write("API_V1_STR=/api/v1\n")
            f.write("BACKEND_CORS_ORIGINS=['http://localhost:8080','http://localhost:3000']\n")
            f.write("AUDIO_SERVICE_URL=http://localhost:9017\n")
            f.write("VIDEO_SERVICE_URL=http://localhost:9018\n")
            f.write("LM_ARENA_SERVICE_URL=http://localhost:8000\n")
        print(f"✅ .env created for harmonic_saas")

    print("\n✅ Setup complete! Run the backend with:")
    print("   cd lm_arena_package && pip install -r config/requirements.txt")
    print("   cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload")

if __name__ == "__main__":
    main()