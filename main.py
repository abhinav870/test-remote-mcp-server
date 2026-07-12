from fastmcp import FastMCP
import os
import aiosqlite
import asyncio

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as conn:
        
        query = """ CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )"""
        
        await conn.execute(query)
        await conn.commit()

asyncio.run(init_db())

@mcp.tool()
async def add_expense(date, amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.'''

    async with aiosqlite.connect(DB_PATH) as conn: # Create a SQLite connection object
        
        query = """
                INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)
                """
        params = [date, amount, category, subcategory, note]

        cursor = await conn.execute(query,params) # Execute the query using sqlite connection object. This returns a cursor object
        await conn.commit()
        
        return {"status": "ok", "id": cursor.lastrowid} # return the id of the row where the data has just been inserted
    
@mcp.tool()
async def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''

    async with aiosqlite.connect(DB_PATH) as conn:    
        query = """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """
        params = [start_date, end_date]

        cursor = await conn.execute(query,params)
        cols = [d[0] for d in cursor.description]

        '''
        cursor.description contains the metadata of each column
        [
            ("id", ...),
            ("date", ...),
            ("amount", ...),
            ("category", ...),
            ("subcategory", ...),
            ("note", ...)
        ]
        So, we fetch the column name by doing d[0]
        '''

        '''
        cursor.fetchall(): This fetches all rows returned by the SQL query.

        rows = [
                    (1, "2026-07-01", 500, "Food"),
                    (2, "2026-07-02", 200, "Travel")
               ]
        '''
        
        res = []
        rows = await cursor.fetchall()
        for row in rows:
            row_dict = dict(zip(cols,row))
            res.append(row_dict)

        return res
        '''
        Same as : 
        return [dict(zip(cols, r)) for r in cursor.fetchall()]
        
        [
            {
                "id": 1,
                "date": "2026-07-01",
                "amount": 500,
                "category": "Food"
            },
            {
                "id": 2,
                "date": "2026-07-02",
                "amount": 200,
                "category": "Travel"
            }
        ]
        '''

@mcp.tool()
async def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    async with aiosqlite.connect(DB_PATH) as conn:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cursor = await conn.execute(query, params)
        cols = [d[0] for d in cursor.description]

        res = []
        rows = await cursor.fetchall()
        for row in rows:
            row_dict = dict(zip(cols,row))
            res.append(row_dict)

        return res
        # return [dict(zip(cols, r)) for r in cursor.fetchall()]

@mcp.tool()
async def delete_expense_id(expense_id: int):
    '''Delete an expense entry using its expense ID.'''

    async with aiosqlite.connect(DB_PATH) as conn:
        query = (

            """
            DELETE from expenses
            WHERE id = ?
            """ 
        )

        params = [expense_id]
        cursor = await conn.execute(query, params)
        await conn.commit()

        if cursor.rowcount == 0:
            return "This ID doesn't exist in the Database"
        
        else:
            return "Deletion Successful"
        
@mcp.tool()
async def edit_expense_id(expense_id: int):
    '''Edit an expense entry using its expense ID.'''
    pass

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    # mcp.run(transport='http', host= '0.0.0.0', port=8000)
    mcp.run(transport="http", host="127.0.0.1", port=8000)