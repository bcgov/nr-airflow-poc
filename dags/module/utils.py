import json

def open_json_file(file: str) -> str:
    """
    Given a JSON file (with path and name), returns its properties.
    """
    try:
        with open(file) as config_file:
            return json.load(config_file)    
    except FileNotFoundError:
        raise Exception('JSON file not found.')
    except Exception as e:    
        raise Exception('Exception message: {}'.format(e))         

def get_query_from_file(path: str, file: str) -> str:
    """
    Given a SQL file, returns a string with the file query content.
    """
    try:        
        with open(path+file, 'r', encoding='utf-8') as qryfile:
            query = qryfile.read()
        return query
    except FileNotFoundError:
        raise Exception('File not found')
    except Exception as e:
        raise Exception('Exception message: {}'.format(e))

def format_temp_table_name(table_metadata: str):
    """
    Returns the temporary table name to be used in the ETL process.
    The table name is extracted from the table_metadata and reduced to the first 26 characters
    so that it does not exceed 30 characters - Oracle limitation over max objects names length.
    The 'tmp_' prefix is then added.
    """
    try:
        return 'tmp_{}'.format(table_metadata['table_name'][:26]).lower()
    except Exception as e:
        raise Exception('Exception message: {}'.format(e))

def add_incremental_date_to_query(query: str, inc_date: str, db_type: str):
    """
    Adds a date filter to a select query in order to perform an incremental extraction.
    """  
    if db_type == 'ORACLE':
        query = ''.join([query, " >= TO_DATE('", inc_date[:16], "', '", 'YYYY-MM-DD HH24:MI', "') + INTERVAL '-3' HOUR"])
    if db_type == 'POSTGRES':
        query = ''.join([query, " >= TO_TIMESTAMP('", inc_date[:16], "', '", 'YYYY-MM-DD HH24:MI', "') + INTERVAL '-3' HOUR"])

    return query
    
def metadata_to_create_table_qry(table_metadata: str):
    """
    Returns a create table statement based on the table's metadata defined on the JSON file for
    a temporary table used in the ETL process.
    The table created will be named with the 26 characters of the table_name property with 'tmp_'
    prefix.
    Works both for ORACLE and POSTGRES databases.
    """
    try:
        columns = table_metadata['columns']
        
        query = 'CREATE TABLE {} ('.format(format_temp_table_name(table_metadata))

        for key in columns:
            query = ''.join([query, key, ' ', columns[key], ','])

        query = query
        query = ''.join([query.rstrip(query[-1]), ')'])
        return query
    except Exception as e:
        raise Exception('Exception message: {}'.format(e))

def metadata_to_drop_table_qry(table_metadata: str):
    """
    Returns a 'DROP TABLE...' statement based on the table's metadata defined on the JSON file for
    a temporary table used in the ETL process.
    The table to be droped will be named with the 26 characters of the table_name property with 
    'tmp_' prefix.
    Works both for ORACLE and POSTGRES databases.
    """
    try:
        return 'DROP TABLE {}'.format(format_temp_table_name(table_metadata))
    except Exception as e:
        raise Exception('Exception message: {}'.format(e))

def metadata_to_insert_qry(table_metadata: str):
    """
    Returns a "INSERT INTO ... SELECT FROM ..." statement based on the table's metadata defined 
    on the JSON file.
    The statement is build to select data from the temporary table earlier created that is not 
    in the final table defined in the table_name property and then perform the insertion.
    Works both for ORACLE and POSTGRES databases.
    """
    try:
        columns = table_metadata['columns']
        primary_keys = table_metadata['primary_key']
        
        columns_str = ''
        columns_t1_str = ''
        primary_keys_str = ''
        
        query = 'INSERT INTO {} ('.format(table_metadata['table_name'])

        for key in columns:
            columns_str = ''.join([columns_str, key, ','])
            columns_t1_str = ''.join([columns_t1_str, 't1.', key, ','])
            
        if len(primary_keys) > 1:
            for i in range(len(primary_keys)):
                if i == 0:
                    pass
                else:
                    primary_keys_str = ''.join([' AND t1.', primary_keys[i], ' = t2.', primary_keys[i]])

        query = ''.join([
            query, 
            columns_str.rstrip(columns_str[-1]), 
            ') SELECT ', 
            columns_t1_str.rstrip(columns_str[-1]), 
            ' FROM ', 
            format_temp_table_name(table_metadata), 
            ' t1 LEFT JOIN ',
            table_metadata['table_name'],
            ' t2 ON t1.',
            primary_keys[0],
            ' = t2.',
            primary_keys[0],
            primary_keys_str,
            ' WHERE t2.',
            primary_keys[0],
            ' IS NULL'
        ])
        return query
    except Exception as e:
        raise Exception('Exception message: {}'.format(e))

def metadata_to_postgres_update_qry(table_metadata: str):
    """
    Returns an update statement based on the table's metadata defined on the JSON file
    for POSTGRES databases.
    The statement is build to select data from the temporary table earlier created and 
    update its values on the table defined in the table_name property.
    """
    try:
        columns = table_metadata['columns']
        primary_keys = table_metadata['primary_key']
        
        columns_str = ''
        primary_keys_str = ''

        query = 'UPDATE {} t1 SET '.format(table_metadata['table_name'])

        for key in columns:
            if key not in primary_keys:
                columns_str = ''.join([columns_str, key, ' = t2.', key, ','])
            
        if len(primary_keys) > 1:
            for i in range(len(primary_keys)):
                if i == 0:
                    pass
                else:
                    primary_keys_str = ''.join([' AND t1.', primary_keys[i], ' = t2.', primary_keys[i]])

        query = ''.join([
            query, 
            columns_str.rstrip(columns_str[-1]), 
            ' FROM ',
            format_temp_table_name(table_metadata),
            ' t2 WHERE t1.',
            primary_keys[0],
            ' = t2.',
            primary_keys[0],
            primary_keys_str
        ])
        return query
    except Exception as e:
        raise Exception('Exception message: {}'.format(e))

def metadata_to_oracle_update_qry(table_metadata: str):
    """
    Returns a merge statement based on the table's metadata defined on the JSON file
    for ORACLE databases.
    The statement is build to select data from the temporary table earlier created and 
    update its values on the table defined in the table_name property.
    """
    try:
        columns = table_metadata['columns']
        primary_keys = table_metadata['primary_key']
        
        columns_str = ''
        columns_t1_str = ''
        primary_keys_str = ''

        query = 'MERGE INTO {} t1 USING {} t2 ON ('.format(table_metadata['table_name'], format_temp_table_name(table_metadata))

        for key in columns:
            if key not in primary_keys:
                columns_str = ''.join([columns_str, 't1.', key, ' = t2.', key, ','])
            
        if len(primary_keys) > 1:
            for i in range(len(primary_keys)):
                if i == 0:
                    pass
                else:
                    primary_keys_str = ''.join([' AND t1.', primary_keys[i], ' = t2.', primary_keys[i]])

        query = ''.join([
            query, 
            't1.',
            primary_keys[0],
            ' = t2.',
            primary_keys[0],
            primary_keys_str,
            ') WHEN MATCHED THEN UPDATE SET ',
            columns_str.rstrip(columns_str[-1])
        ])
        return query
    except Exception as e:
        raise Exception('Exception message: {}'.format(e))