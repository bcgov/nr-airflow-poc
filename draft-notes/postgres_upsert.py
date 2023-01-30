import sqlalchemy as db
import pandas as pd
from typing import Optional, Dict

def create_upsert_method(meta: db.MetaData, extra_update_fields: Optional[Dict[str, str]]):
    """
    Create upsert method that satisfied the pandas's to_sql API.
    """
    def method(table, conn, keys, data_iter):
        # select table that data is being inserted to (from pandas's context)
        sql_table = db.Table(table.name, meta, autoload=True)
        
        # list of dictionaries {col_name: value} of data to insert
        values_to_insert = [dict(zip(keys, data)) for data in data_iter]
        
        # create insert statement using postgresql dialect.
        # For other dialects, please refer to https://docs.sqlalchemy.org/en/14/dialects/
        insert_stmt = db.dialects.postgresql.insert(sql_table, values_to_insert)

        # create update statement for excluded fields on conflict
        update_stmt = {exc_k.key: exc_k for exc_k in insert_stmt.excluded}
        if extra_update_fields:
            update_stmt.update(extra_update_fields)
        
        # create upsert statement. 
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=sql_table.primary_key.columns, # index elements are primary keys of a table
            set_=update_stmt # the SET part of an INSERT statement
        )
        
        # execute upsert statement
        conn.execute(upsert_stmt)

    return method

# create postgres db engine
db_engine = db.create_engine(f"postgresql://{user}:{password}@{host}:5432/{database}")

df = pd.DataFrame({
  'id': [10, 20],
  'updated_at': [pd.to_datetime(1490195805, unit='s'), pd.to_datetime(1490205805, unit='s')]
})

# create DB metadata object that can access table names, primary keys, etc.
meta = db.MetaData(db_engine)

# dictionary which will add additional changes on update statement. I.e. all the columns which are not present in DataFrame,
# but needed to be updated regardless. The common example is `updated_at`. This column can be updated right on SQL server, instead of in pandas DataFrame
extra_update_fields = {"updated_at": "NOW()"}

# create upsert method that is accepted by pandas API
upsert_method = create_upsert_method(meta, extra_update_fields)

# perform upsert of df DataFrame values to a table `table_name` and Postgres connection defined at `db_engine`
df.to_sql(
  table_name,
  db_engine
  schema=db_schema,
  index=False,
  if_exists="append",
  chunksize=200, # it's recommended to insert data in chunks
  method=upsert_method
)