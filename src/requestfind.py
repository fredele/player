import urllib
import re
import time
import copy
import hashlib

def Requestfind(request: dict, db, query_hash = None) -> dict:
    """
    Standalone recalculation of a saved query.
    No Flask / app dependency.
    """

    page_nbr = int(request.get("page_nbr", 0))
    response_count = int(request.get("response_count", 1500))
    key = urllib.parse.unquote(request.get("field", ""))
    sorttag_raw = request.get("sorttag", key)
    sorttag = urllib.parse.unquote(sorttag_raw.split("$", 1)[0])

    if "sort" in request:
        sort = urllib.parse.unquote(str(request["sort"]))
    else:
        parts = sorttag_raw.split("$", 1)
        sort = parts[1] if len(parts) == 2 else "ASCENDING"

    sort = -1 if sort.upper() == "DESCENDING" else 1
    display = urllib.parse.unquote(request.get("display", ""))
    full = str(request.get("full", "false")).lower()

    strquery = urllib.parse.unquote(request.get("query", ""))
    if strquery in ("", "null", "None"):
        return {"key": key, "result": [], "page_nbr": page_nbr, "query": ""}

    # ------------------------------------------------------------------
    # Replace $time_XXX$ placeholders
    # ------------------------------------------------------------------
    tags = re.findall(r"\$time_(\d+)\$", strquery)
    vals = {}
    now = int(time.time())
    for ct in tags:
        try:
            vals[f"$time_{ct}$"] = now - int(ct)
        except ValueError:
            pass

    def replacetime(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    for placeholder, value in vals.items():
                        if placeholder in v:
                            obj[k] = value
                else:
                    replacetime(v)
        elif isinstance(obj, list):
            for item in obj:
                replacetime(item)
        return obj

    try:
        query = eval(strquery, {"__builtins__": {}}, {})  # still risky, but isolated
    except Exception:
        return {"key": key, "result": [], "page_nbr": page_nbr, "query": strquery}

    query = replacetime(query)
    basequery = copy.deepcopy(query)

    # ------------------------------------------------------------------
    # Display / count tags
    # ------------------------------------------------------------------
    display_tags = re.findall(r"\$([a-zA-Z0-9_]+)\$", display)
    counttags = [t.replace("_count", "") for t in display_tags if t.endswith("_count")]
    displaytags = [t for t in display_tags if not t.endswith("_count")]

    # Last filter (used for alphabet / group_ filters)
    lastfield = None
    lastfieldvalue = None
    if "$and" in query and query["$and"]:
        last = query["$and"][-1]
        if isinstance(last, dict) and last:
            lastfield = next(iter(last.keys()))
            lastfieldvalue = last[lastfield]

    # Full albums mode
    if full == "true":
        #dirhash_values = db.mediafiles.find(basequery).distinct("dirhash")
        
         # On demande uniquement le champ 'dirhash' à MongoDB pour économiser la RAM
        cursor_dirhash = db.mediafiles.find(basequery, {dirhash: 1})

        # On utilise un 'set' Python pour éliminer les doublons instantanément à la volée
        dirhash_values = list({doc[dirhash] for doc in cursor_dirhash if dirhash in doc})

        basequery = {"$and": [{"dirhash": {"$in": dirhash_values}}]}

    # ------------------------------------------------------------------
    # Hash
    # ------------------------------------------------------------------

    try:
        s = (
            urllib.parse.quote(str(query))
            + str(sort)
            + sorttag
            + display
            + str(page_nbr)
            + str(response_count)
            + full
        )
        has = query_hash or hashlib.sha256(s.encode("utf-8")).hexdigest()
    except Exception:
        return {"key": key, "result": [], "page_nbr": page_nbr, "query": ""}

    

    try:
        cursorsavedquery = db.savedqueries.find({'hashquery': has})
        cs = [x for x in cursorsavedquery]
        if len(cs) >= 1:
            result = cs[0]['''result''']
            q = cs[0]['''query''']
            # Query has been found, return it ... and update the count !
            db.savedqueries.update_one({'hashquery': has}, {"$set": {"displayed": 1 + cs[0]["displayed"]}})
            return { 'key': key, 'result': result , 'page_nbr' : page_nbr,"query" :q }
    except:
        json_resp({'response': 'Error', })
 
    
    
    
    
    # ------------------------------------------------------------------
    # Aggregation pipeline
    # ------------------------------------------------------------------
    grp: Dict[str, Any] = {
        "_id": f"${key}",
        "files": {"$sum": 1},
        "dirhashs": {"$addToSet": "$dirhash"},
    }
    prj: Dict[str, Any] = {
        "_id": 0,
        "keyval": "$_id",
        "files": 1,
        "dirhashs": 1,
    }
    tags_used = []

    def add_count_tag(tag: str):
        if tag not in grp:
            grp[f"{tag}_count"] = {"$addToSet": f"${tag}"}
            tags_used.append(tag)
        if f"{tag}_count" not in prj:
            prj[f"{tag}_count"] = {"$size": f"${tag}_count"}

    def add_display_tag(tag: str):
        if tag not in grp:
            grp[tag] = {"$addToSet": f"${tag}"}
            tags_used.append(tag)
        if tag not in prj:
            prj[tag] = f"${tag}"

    for tag in counttags:
        add_count_tag(tag)
    for tag in displaytags:
        add_display_tag(tag)

    # Sort values for pagination
    try:
        #sortvals = sorted(db.mediafiles.find(basequery).distinct(sorttag))
        
        cursor_sorttag = db.mediafiles.find(basequery, {sorttag: 1})
        sortvals =  list({
        v for doc in cursor_sorttag if sorttag in doc
        for v in (doc[sorttag] if isinstance(doc[sorttag], list) else [doc[sorttag]])
        })
        
        
    except Exception:
        sortvals = sorted(str(x) for x in db.mediafiles.find(basequery).distinct(sorttag))

        
    if sort == -1:
        sortvals.reverse()

    start = page_nbr * response_count
    end = start + response_count
    sortvals_page = sortvals[start:end]

    if not sortvals_page:
        result = []
    else:
        q = copy.deepcopy(basequery)
        if "$and" not in q:
            q["$and"] = []
        q["$and"].append({sorttag: {"$in": sortvals_page}})

        pipeline = [
            {"$match": q},
            {"$unwind": f"${key}"},
            {"$group": grp},
            {"$project": prj},
            {"$sort": {sorttag: sort}},
        ]

        result = list(db.mediafiles.aggregate(pipeline))

        # Flatten nested lists
        for doc in result:
            for tag in tags_used:
                if tag in doc and isinstance(doc[tag], list) and doc[tag] and isinstance(doc[tag][0], list):
                    doc[tag] = [item for sublist in doc[tag] for item in sublist]

        # Keep only rows that belong to the current page of sort values
        result = [
            r for r in result
            if r.get("keyval") not in ("", [""])
            and (not r.get(sorttag) or r[sorttag][0] in sortvals_page)
        ]

    # ------------------------------------------------------------------
    # Alphabet / group_ post-filters
    # ------------------------------------------------------------------
    if lastfield and "alphabet" in lastfield and key != "dirhash":
        try:
            result = [
                i for i in result
                if str(i["keyval"]).lower().startswith(str(lastfieldvalue).lower())
            ]
        except Exception:
            pass

    if lastfield and "group_" in lastfield and key != "dirhash":
        try:
            def char_pos(c):
                return ord(c.lower()) - ord("a") if c.isalpha() else 0

            result = [
                i for i in result
                if char_pos(lastfieldvalue[0]) <= char_pos(str(i["keyval"])[0])
                <= char_pos(lastfieldvalue[-1])
            ]
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Build display strings + nested queries
    # ------------------------------------------------------------------
    def displayed(r, val):
        try:
            v = r.get(val)
            if isinstance(v, list):
                return ", ".join(str(e) for e in v)
            return str(v)
        except Exception:
            return ""

    for r in result:
        try:
            nested = copy.deepcopy(basequery)
            if "$and" not in nested:
                nested["$and"] = []
            nested["$and"].append({key: r["keyval"]})
            r["query"] = urllib.parse.quote(str(nested).encode("utf-8"))

            displayval = display
            displayval = displayval.replace(f"${key}$", displayed(r, "keyval"))
            displayval = displayval.replace(f"${sorttag}$", displayed(r, sorttag))
            for tag in displaytags:
                displayval = displayval.replace(f"${tag}$", displayed(r, tag))
            for tag in counttags:
                displayval = displayval.replace(f"${tag}_count$", displayed(r, f"{tag}_count"))

            r["display"] = displayval or r["keyval"]
            r["covers"] = r.pop("dirhashs", [])
        except Exception as e:
            print(f"display build error: {e}")

    # ------------------------------------------------------------------
    # Persist the result
    # ------------------------------------------------------------------
    q_str = urllib.parse.quote(str(basequery))
    try:
        db.savedqueries.update_one(
            {"hashquery": has},
            {
                "$set": {
                    "hashquery": has,
                    "query": q_str,
                    "lasttime": int(time.time()),
                    "field": key,
                    "sort": sort,
                    "sorttag": sorttag,
                    "display": display,
                    "full": full == "true",
                    "displayed": 0,
                    "result": result,
                    "page_nbr": page_nbr,
                    "response_count": response_count,
                }
            },
            upsert=True,
        )
        print(f"Updated hash: {has}")
    except Exception as e:
        print(f"Failed to save query {has}: {e}")

    return {
        "key": key,
        "page_nbr": page_nbr,
        "query": q_str,
        "result": result,
    }
