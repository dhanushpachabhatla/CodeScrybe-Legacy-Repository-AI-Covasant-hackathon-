from dotenv import load_dotenv
import os
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(dotenv_path=env_path)
print(os.getenv("NEO4J_URI"))