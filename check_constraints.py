import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(os.getenv("SUPABASE_DB_URL"))
query = "SELECT conname, contype FROM pg_constraint WHERE contype = chr(112) OR contype = chr(102)"
with engine.connect() as conn:
    result = conn.execute(text(query))
    constraints = list(result)
    print("Contraintes PK/FK trouvees:", len(constraints))
    for c in constraints:
        print(" -", c[0], "(type:", c[1], ")")
