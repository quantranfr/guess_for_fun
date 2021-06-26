import pandas as pd
df = pd.read_csv('clan_progression.csv')
print(f"data.addColumn('number', 'Day');")
for col in df.columns:
    print(f"data.addColumn('number', '{col}');")

print("data.addRows([")
for i, r in df.iterrows():
    print(f"[{i+1}, {', '.join(map(lambda x: str(x), r.values))}],")
print("]);")
