from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import pymongo
import jwt
from bson.objectid import ObjectId

client = pymongo.MongoClient("mongodb+srv://root:notesroot@cluster0.dm8n2b2.mongodb.net/?retryWrites=true&w=majority")
db = client["notes-app-database"]
users = db["users"]
notes = db["notes"]

app = Flask(__name__)
cors = CORS(app)


# @app.after_request
# def after_request(response):
#     print("CORS is here")
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,auth-token')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
#     return response
"""Authorisation endpoint"""

@app.route("/api/auth/login",methods=["POST"])
def login():
    if request.method=="POST":
        username = request.json["username"]
        password = request.json["password"]
        if(users.count_documents({"username":username})==0):
            return jsonify({"status":404,"message":"No user found with the specified username"})
        else:
            x = users.find_one({"username":username})
            if(x["password"]==password):
                payload = {"user":str(x["_id"])}
                print(payload)
                token = jwt.encode(payload=payload,key="secret")
                return jsonify({"status":200,"auth-token":token ,"message":"User logged in"})
            else:
                return jsonify({"status":404,"message":"Invalid credentials"})

@app.route("/api/auth/signup",methods=["POST"])
def signup():
    if request.method=="POST":
        email = request.json["email"]
        name = request.json["name"]
        username = request.json["username"]
        password = request.json["password"]
        if(email=='' or name=='' or username=='' or password==''):
            return jsonify({"status":500,"message":"None of the fields cannot be empty"})

        if(users.count_documents({"email":email}) > 0):
            return jsonify({"status":401,"message":"User already exists"})
        else:
            user = {"email":email,"name":name,"username":username,"password":password}
            x = users.insert_one(user)
            if x.acknowledged:
                return jsonify({"status":200,"message":"User created"})

"""NOTES ENDPOINT"""
@app.route("/api/notes/fetchall",methods=["GET"])
def fetchall():
    if request.method=="GET":
        token = request.headers.get("auth-token")
        try:
            user = jwt.decode(token, key="secret",algorithms=["HS256"])["user"]
        except:
            return jsonify({"status":404,"message":"Invalid auth token"})

        userNotes = notes.find({"user":user})
        allNotes = []
        for i in userNotes:
            allNotes.append(i)
        for i in allNotes:
            i["_id"] = str(i["_id"])
        return jsonify({"status":200,"notes":allNotes})

@app.route("/api/notes/addnote",methods=["POST"])
def addnote():
    if request.method=="POST":
        token = request.headers.get("auth-token")
        title = request.json["title"]
        desc = request.json["desc"]
        try:
            user = jwt.decode(token, key="secret",algorithms=["HS256"])["user"]
        except:
            return jsonify({"status":404,"message":"Invalid auth token"})
        if title=="" or desc=="":
            return jsonify({"status":401,"message":"Neither title nor description cannot be empty"})
        note = {"user":user, "title":title,"desc":desc}
        x = notes.insert_one(note)
        note = notes.find_one({"_id":x.inserted_id})
        note["_id"] = str(note["_id"])
        if x.acknowledged:
            return jsonify({"status":200,"message":"Note added","note":note})

@app.route("/api/notes/editnote",methods=["PUT"])
def editnote():
    if request.method=="PUT":
        token = request.headers.get("auth-token")
        title = request.json["title"]
        desc = request.json["desc"]
        id = request.json["id"]
        try:
            user = jwt.decode(token, key="secret",algorithms=["HS256"])["user"]
        except:
            return jsonify({"status":401,"message":"Invalid auth token"})
        note = notes.find_one({"_id":ObjectId(id)})
        if note["user"]==user:
            newNote = notes.find_one_and_update({"_id":ObjectId(id)},{"$set":{"title":title,"desc":desc}},return_document=pymongo.ReturnDocument.AFTER)
            print(newNote)
            newNote["_id"] = str(newNote["_id"])
            return jsonify({"status":201,"message":"note edited","note":newNote})
        else:
            return jsonify({"status":404,"message":"Authorisation denied"})


@app.route("/api/notes/deletenote",methods=["DELETE"])
def deletenote():
    if  request.method == "DELETE":
        token = request.headers.get("auth-token")
        id = request.json["id"]
        print("id:   ",id)
        try:
            user = jwt.decode(token, key="secret",algorithms=["HS256"])["user"]
        except:
            return jsonify({"status":404,"message":"Invalid auth token"})
        note = notes.find_one({"_id":ObjectId(id)})
        if note["user"]==user:
            deletedNote = notes.find_one_and_delete({"_id":ObjectId(id)})
            deletedNote["_id"] = str(deletedNote["_id"])
            return jsonify({"status":201,"message":"Note deleted","note":deletedNote})
        else:
            return jsonify({"status":404,"message":"Authorisation denied"})
        

if __name__=="__main__":
    app.run(debug=True)