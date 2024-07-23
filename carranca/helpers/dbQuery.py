

#import pandas as pd
from sqlalchemy import create_engine, text
from ..shared import app_config

engine = create_engine(
    app_config.SQLALCHEMY_DATABASE_URI,
    isolation_level = "READ UNCOMMITTED",
    connect_args={'connect_timeout': 600}
)

def executeSQL(sql):
    global engine
    with engine.connect() as conn:
        return conn.execute(text(sql))

def getValues(sql):
    rows = executeSQL(sql)
    try:
        lines = rows.fetchall()
        l = []
        if len(lines) > 1:
            for line in lines:
                l.append(line[0])
            return tuple(l)
        elif len(lines[0]) > 1:
            for v in lines[0]:
                l.append(v)
            return tuple(l)
        else:
            return lines[0][0]
    except:
        return None

def getLastId(tabeName: str)->int:
    return getValues(f"SELECT IDENT_CURRENT('{tabeName}')")

def getDictResultSet(sql):
    return {row[0]: row[1] for row in executeSQL(sql)}

# mgd 2024.05.11
# def getListDictResultset(sql):
#     df = getDataframeResultset(sql)
#     ret = []
#     for _, row in df.iterrows():
#         dic = {}
#         for i in range(len(row)):
#             dic[df.columns[i]] = row[i]
#         ret.append(dic)
#     return ret

# def getDictFieldNamesValuesResultset(sql):
#     df = getDataframeResultset(sql)
#     row = df.iloc[0]
#     dic = {}
#     for i in range(len(row)):
#         dic[df.columns[i]] = row[i]
#     return dic

# def getJSONStrResultset(sql):
#     return json.dumps(getListDictResultset(sql)[0])

# def getDataframeResultset(sql):
#     return pd.read_sql(sql, connectDB())

# def getListResultset(sql):
#     return [row[0] for row in executeSQL(sql)]

