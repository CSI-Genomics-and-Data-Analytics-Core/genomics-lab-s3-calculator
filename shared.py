from pathlib import Path
import pandas as pd

app_dir = Path(__file__).parent
ngs_details = pd.read_csv(app_dir / "data/ngs-size.csv")
