import json
from database.db import get_conn

def create_factory(name, business_type, product, country):
    c = get_conn()
    cur = c.execute(
        "INSERT INTO factories(name,business_type,primary_product,country) VALUES(?,?,?,?)",
        (name, business_type, product, country),
    )
    c.commit()
    fid = cur.lastrowid
    c.close()
    return fid

def get_factory(fid):
    c = get_conn()
    row = c.execute("SELECT * FROM factories WHERE id=?", (fid,)).fetchone()
    c.close()
    return dict(row) if row else None

def add_document(factory_id, name, doc_type, path, indexed=1):
    c = get_conn()
    # Replace the metadata row for the same factory/document instead of creating
    # confusing duplicates when a user re-uploads a revised SOP.
    existing = c.execute(
        "SELECT id FROM documents WHERE factory_id=? AND name=?",
        (factory_id, name),
    ).fetchone()
    if existing:
        c.execute(
            "UPDATE documents SET doc_type=?, path=?, indexed=?, created_at=CURRENT_TIMESTAMP WHERE id=?",
            (doc_type, path, indexed, existing["id"]),
        )
        did = existing["id"]
    else:
        cur = c.execute(
            "INSERT INTO documents(factory_id,name,doc_type,path,indexed) VALUES(?,?,?,?,?)",
            (factory_id, name, doc_type, path, indexed),
        )
        did = cur.lastrowid
    c.commit()
    c.close()
    return did

def mark_documents_indexed(factory_id, indexed=True):
    c = get_conn()
    c.execute("UPDATE documents SET indexed=? WHERE factory_id=?", (1 if indexed else 0, factory_id))
    c.commit()
    c.close()

def list_documents(factory_id):
    c = get_conn()
    rows = c.execute(
        "SELECT * FROM documents WHERE factory_id=? ORDER BY created_at DESC",
        (factory_id,),
    ).fetchall()
    c.close()
    return [dict(x) for x in rows]

def add_analysis(factory_id, analysis_type, input_name, status, result):
    c = get_conn()
    cur = c.execute(
        "INSERT INTO analyses(factory_id,analysis_type,input_name,status,result_json) VALUES(?,?,?,?,?)",
        (factory_id, analysis_type, input_name, status, json.dumps(result, ensure_ascii=False)),
    )
    c.commit()
    aid = cur.lastrowid
    c.close()
    return aid

def add_findings(factory_id, analysis_id, findings):
    c = get_conn()
    ids = []
    for f in findings:
        cur = c.execute(
            """INSERT INTO findings(factory_id,analysis_id,title,category,severity,evidence,explanation,recommendation)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                factory_id,
                analysis_id,
                f.get("title", "Untitled"),
                f.get("category", "General"),
                f.get("severity", "Medium"),
                f.get("evidence", ""),
                f.get("explanation", ""),
                f.get("recommendation", ""),
            ),
        )
        ids.append(cur.lastrowid)
    c.commit()
    c.close()
    return ids

def list_findings(factory_id):
    c = get_conn()
    rows = c.execute(
        "SELECT * FROM findings WHERE factory_id=? ORDER BY created_at DESC",
        (factory_id,),
    ).fetchall()
    c.close()
    return [dict(x) for x in rows]

def add_action(factory_id, finding_id, action, preventive_action, responsible, due_date):
    c = get_conn()
    cur = c.execute(
        """INSERT INTO corrective_actions(factory_id,finding_id,action,preventive_action,responsible,due_date)
           VALUES(?,?,?,?,?,?)""",
        (factory_id, finding_id, action, preventive_action, responsible, due_date),
    )
    c.commit()
    aid = cur.lastrowid
    c.close()
    return aid

def list_actions(factory_id):
    c = get_conn()
    rows = c.execute(
        "SELECT * FROM corrective_actions WHERE factory_id=? ORDER BY created_at DESC",
        (factory_id,),
    ).fetchall()
    c.close()
    return [dict(x) for x in rows]

def update_action(action_id, status, evidence=None):
    c = get_conn()
    if evidence is None:
        c.execute("UPDATE corrective_actions SET status=? WHERE id=?", (status, action_id))
    else:
        c.execute(
            "UPDATE corrective_actions SET status=?, evidence=? WHERE id=?",
            (status, evidence, action_id),
        )
    c.commit()
    c.close()
