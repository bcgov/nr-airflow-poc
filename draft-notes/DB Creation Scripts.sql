/**********************************
***** Oracle - Table Creation *****
***********************************/
CREATE TABLE SEEDLOT (
	SEEDLOT_NUMBER VARCHAR2(5),
	VEGETATION_CODE VARCHAR2(8),
	GENETIC_CLASS_CODE VARCHAR2(1),
	ENTRY_USERID VARCHAR2(30),
	ENTRY_TIMESTAMP TIMESTAMP,
	UPDATE_USERID VARCHAR2(30),
	UPDATE_TIMESTAMP TIMESTAMP,
	CONSTRAINT SEEDLOT_PK
		PRIMARY KEY (SEEDLOT_NUMBER)
);

CREATE TABLE FOREST_CLIENT (	
    CLIENT_NUMBER VARCHAR2(8), 
	CLIENT_NAME VARCHAR2(30), 
	ENTRY_USERID VARCHAR2(30), 
	ENTRY_TIMESTAMP TIMESTAMP (6), 
	UPDATE_USERID VARCHAR2(30), 
	UPDATE_TIMESTAMP TIMESTAMP (6), 
	CONSTRAINT FOREST_CLIENT_PK 
        PRIMARY KEY (CLIENT_NUMBER)
);

CREATE TABLE SEEDLOT_OWNER_QUANTITY (	
    SEEDLOT_NUMBER VARCHAR2(5), 
	CLIENT_NUMBER VARCHAR2(8), 
	QTY_RESERVED NUMBER(10, 2), 
	ENTRY_USERID VARCHAR2(30), 
	ENTRY_TIMESTAMP TIMESTAMP (6), 
	UPDATE_USERID VARCHAR2(30), 
	UPDATE_TIMESTAMP TIMESTAMP (6), 
	CONSTRAINT SEEDLOT_OWNER_QUANTITY_PK 
        PRIMARY KEY (SEEDLOT_NUMBER, CLIENT_NUMBER),
    CONSTRAINT SEEDLOT_OWN_QTY_SEEDLOT_FK
        FOREIGN KEY (SEEDLOT_NUMBER)
        REFERENCES SEEDLOT(SEEDLOT_NUMBER),
    CONSTRAINT SEEDLOT_OWN_QTY_FORE_CLIENT_FK
        FOREIGN KEY (CLIENT_NUMBER)
        REFERENCES FOREST_CLIENT(CLIENT_NUMBER)
);

/************************************
***** Postgres - Table Creation *****
*************************************/
CREATE TABLE SEEDLOT (
	SEEDLOT_NUMBER VARCHAR(5),
	VEGETATION_CODE VARCHAR(8),
	GENETIC_CLASS_CODE VARCHAR(1),
	ENTRY_USERID VARCHAR(30),
	ENTRY_TIMESTAMP TIMESTAMP,
	UPDATE_USERID VARCHAR(30),
	UPDATE_TIMESTAMP TIMESTAMP,
	CONSTRAINT SEEDLOT_PK
		PRIMARY KEY (SEEDLOT_NUMBER)
);

CREATE TABLE FOREST_CLIENT (	
    CLIENT_NUMBER VARCHAR(8), 
	CLIENT_NAME VARCHAR(30), 
	ENTRY_USERID VARCHAR(30), 
	ENTRY_TIMESTAMP TIMESTAMP (6), 
	UPDATE_USERID VARCHAR(30), 
	UPDATE_TIMESTAMP TIMESTAMP (6), 
	CONSTRAINT FOREST_CLIENT_PK 
        PRIMARY KEY (CLIENT_NUMBER)
);

CREATE TABLE SEEDLOT_OWNER_QUANTITY (	
    SEEDLOT_NUMBER VARCHAR(5), 
	CLIENT_NUMBER VARCHAR(8), 
	QTY_RESERVED DECIMAL(10, 2), 
	ENTRY_USERID VARCHAR(30), 
	ENTRY_TIMESTAMP TIMESTAMP (6), 
	UPDATE_USERID VARCHAR(30), 
	UPDATE_TIMESTAMP TIMESTAMP (6), 
	CONSTRAINT SEEDLOT_OWNER_QUANTITY_PK 
        PRIMARY KEY (SEEDLOT_NUMBER, CLIENT_NUMBER),
    CONSTRAINT SEEDLOT_OWN_QTY_SEEDLOT_FK
        FOREIGN KEY (SEEDLOT_NUMBER)
        REFERENCES SEEDLOT(SEEDLOT_NUMBER),
    CONSTRAINT SEEDLOT_OWN_QTY_FORE_CLIENT_FK
        FOREIGN KEY (CLIENT_NUMBER)
        REFERENCES FOREST_CLIENT(CLIENT_NUMBER)
);

/***************************************
***** Postgres - Insert Statements *****
****************************************/
INSERT INTO SEEDLOT VALUES 
	('0001', 'VEG1', 'A', 'USER1', CURRENT_TIMESTAMP, 'USER1', CURRENT_TIMESTAMP),
	('0002', 'VEG2', 'A', 'USER1', CURRENT_TIMESTAMP, 'USER1', CURRENT_TIMESTAMP),
	('0003', 'VEG3', 'B', 'USER2', CURRENT_TIMESTAMP, 'USER2', CURRENT_TIMESTAMP),
	('0004', 'VEG4', 'B', 'USER2', CURRENT_TIMESTAMP, 'USER2', CURRENT_TIMESTAMP),
	('0005', 'VEG5', 'B', 'USER2', CURRENT_TIMESTAMP, 'USER2', CURRENT_TIMESTAMP);

INSERT INTO FOREST_CLIENT VALUES 
	('0001', 'Company 1', 'USER1', CURRENT_TIMESTAMP, 'USER1', CURRENT_TIMESTAMP),
	('0002', 'Company 2', 'USER2', CURRENT_TIMESTAMP, 'USER2', CURRENT_TIMESTAMP);

INSERT INTO SEEDLOT_OWNER_QUANTITY VALUES 
	('0001', '0001', 900, 'USER1', CURRENT_TIMESTAMP, 'USER1', CURRENT_TIMESTAMP),
	('0001', '0002', 600, 'USER1', CURRENT_TIMESTAMP, 'USER1', CURRENT_TIMESTAMP),
	('0002', '0001', 300, 'USER1', CURRENT_TIMESTAMP, 'USER1', CURRENT_TIMESTAMP),
	('0003', '0002', 450, 'USER1', CURRENT_TIMESTAMP, 'USER1', CURRENT_TIMESTAMP);

/***************************************
***** Postgres - Update Statements *****
****************************************/
UPDATE SEEDLOT
SET VEGETATION_CODE = 'XXX',
    UPDATE_TIMESTAMP = CURRENT_TIMESTAMP
WHERE SEEDLOT_NUMBER IN ('0001', '0002');

INSERT INTO FOREST_CLIENT VALUES 
	('9999', 'Company 9999', 'USER9', CURRENT_TIMESTAMP, 'USER9', CURRENT_TIMESTAMP);