#!/usr/bin/env python3
"""
WMS-API bindings for puthon,
conatining a general wmsapi class,
and a easy-to-use kiddies class.
"""

import requests
import json
import os
import datetime

debug = True

class wms:
    """
    Weather Monitoring System interface in python.
    Wrapper of the wmsapi.wmsapi class, to be as similar to the web interface
    as possible.

    This class should be able to login, get diagnostics, upload, and delete
    images, maybe downloading

    Usage:
        api = wms(\"url\")
        api.login(\"username\", \"password\")
        api.folderContents(\"foldername\")
        api.addimg(\"path/to/img\", \"foldername\")
        api.deloldestimg(\"foldername\")
    """
    def __init__(self, url="http://wms.viwetter.de/api/index.php"):
        self.api = None
        self.user = "default"
        self.url = url
        self.api_start = datetime.datetime.now()
        self.errormsg = "[ERROR] not logged in"

    def interact(self):
        """
        login via command-line input, without showing the password
        """
        import getpass
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        return self.login(username, password)

    def login(self, username, password):
        """
        log into the Weather Monitoring System.
        returns true is successfull.

        arguments:
        username -- wms-username
        password -- self explanatory
        """
        self.api = wmsapi(username, password, self.url)
        self.user = username
        self.session_start = datetime.datetime.now()
        return self.api.ping()

    def folderContents(self, identifier):
        """
        returns an array with dictionaries for every entry with <identifier> as
        it's folder id.

        arguments:
        identifier -- folder id or name
        """
        if type(identifier)==str:
            identifier = self.api.translateFolder(identifier)
        entr = self.api.getTableDict("entries")
        entrList = []
        for en in entr:
            if int(en["fid"]) == identifier:
                entrList.append(en)
        return entrList

    def addimg(self, image, identifier):
        """
        figures out how to add image (remote/upload)
        then contacts the server.
        Returns the post answer or False on error

        arguments:
        image      -- path to the image (url/path)
        identifier -- target folder (id)
        """
        if not self.api.ping():
            print(self.errormsg)
            return False
        if type(identifier)==str:
            identifier = self.api.translateFolder(identifier)
        remstart = ["http://","https://","ftp://"]
        isremote = False
        for beg in remstart:
            if image.startswith(beg):
                isremote = True
                break
        if isremote:
            # TODO: remote linking files
            pass
        else:
            return self.api.newCycle(image,identifier)

    def deloldestimg(self, identifier):
        """
        Deletes the oldest image in the folder with <identifier> id.
        Returns the post answer or False on error

        arguments:
        identifier -- folder name or id
        """
        if not self.api.ping():
            print(self.errormsg)
            return False
        if type(identifier)==str:
            identifier = self.api.translateFolder(identifier)
        return self.api.delLastCycle(identifier)

    def deleteById(self, imgid):
        """

        """
        # TODO: delete by id
        pass # delete image by image id

    def createFolder(self, foldername):
        # TODO: create folder
        pass # return folder id

    def deleteFolder(self, identifier):
        # TODO: delete folder
        pass # return successfull

    def downloadimg(self, id, tofile):
        # TODO: download image
        pass # save image with id to tofile


class wmsapi:
    """
    general wms-api class
    constructed with username and password
    wmsapi.wmsapi(username, password [, url])
    """

    def __init__(self, username, password, url="http://wms.viwetter.de/api/index.php"):
        """
        Constructor for the wmsapi.
        """
        self.username = username
        self.password = password
        self.url = url

    def post(self, data=None, files=None):
        """
        general post request handler
        uses self.url as request target

        arguments:
        data  -- post data (fills username and password if not provided)
        files -- files array
        """
        if not data:
            data = {"username":self.username,"password":self.password}
        if "username" not in data:
            data["username"]=self.username
        if "password" not in data:
            data["password"]=self.password
        r = requests.post(self.url, data=data, files=files)
        return r

    def ping(self):
        """
        returns true if the server is up and the login data is correct,
        otherwise false
        """
        return valid(self.url, self.username, self.password)

    def prepfile(self, path):
        """
        opens file in the correct format to be sent over post

        arguments:
        path -- path to file
        """
        return open(path, "rb")


    def uploadfile(self, path, data=None):
        """
        tries to upload file at <path> to self.url
        <data> is passed through, and necessary for the server
        to accept the file(s)

        arguments:
        path -- path to file
        data -- post data
        """
        f = self.prepfile(path)
        ans = self.post(data, {"file": f})
        f.close()
        return ans

    def remoteUpload(self, url, target):
        pass # TODO: remote upload

    def newCycle(self, path, target):
        """
        adds file at <path> to folder with <target> id
        to query for the id use getTableDict(table)

        arguments:
        path   -- path to file
        target -- target folder id
        """
        data = {"target": target, "function": "newcycle"}
        ret = self.uploadfile(path, data)
        if debug:
            print(ret.text)
        return ret

    def writeGlobalLog(self, ltype, text):
        """
        writes [LTYPE] text << time
        to the global servers log.
        """
        return requests.get(self.url, params={"t":ltype,"d":text})


    def delLastCycle(self, target):
        """
        deletes oldst file from folder target

        arguments:
        target -- target folder id
        """
        data = {"target": target, "function": "deloldest"}
        return self.post(data)

    def getFolderSize(self, target):
        """
        returns the number of active files in folder with id <target>
        if non-existant returns 0

        arguments:
        target -- target folder id
        """
        data = {"target": target, "function": "dirsize"}
        return int(self.post(data).text)

    def getTableJson(self, table):
        """
        returns a json string from table <table>
        can be a huge amout of text to be received
        raises LookupError when table doesn't exist

        arguments:
        table -- name of the table [entries, folders, logins]
        """
        if table in ["entries", "folders", "logins"]:
            return self.post({"function":"tablejson", "table": table}).text
        else:
            raise LookupError(str(table) + " not a table")

    def getTableDict(self, table):
        """
        return a dictionary containing all rows from table <table>
        raises LookupError when table doesn't exist

        arguments:
        table -- name of the table [entries, folders, logins]
        """
        return json.loads(self.getTableJson(table))

    def translateFolder(self, identifier):
        """
        Queries the API for tables.
        if <identifier> is of type int, returns the name of the folder with
        id <identifier> as a str.
        if <identifier> is of type str, returns the id of the folder with
        str <identifier> as it's name.

        arguments:
        identifier -- id or name of folder
        """
        folders = self.getTableDict("folders")
        if type(identifier) == int:
            for row in folders:
                if int(row["id"])==identifier:
                    return row["folder"]
            raise LookupError("no folder with that id")
        elif type(identifier) == str:
            for row in folders:
                if row["folder"]==identifier:
                    return int(row["id"])
            raise LookupError("no folder with that name")
        raise ValueError("identifier in unknown format")

    def nicePrintTables(self, tofile=None):
        """
        Printing contents of all tables to console or to a
        file if <tofile> is set

        arguments:
        tofile -- destination file (overwrites file)
        """
        dicts = []
        ellipse = 10
        tables = ["entries", "folders", "logins"]
        if tofile:
            with open(tofile, "w") as f: pass
        for tab in tables:
            dicts.append(self.getTableDict(tab))
        for d in dicts:
            form = ""
            length = {}
            for row in d:
                for key in row:
                    if len(row[key])>ellipse:
                        row[key] = row[key][:ellipse+1]+"..."
                    if key in length:
                        if len(row[key])>length[key]:
                            length[key]=len(row[key])
                    else:
                        length[key]=0
            keyname = {}
            for key in d[0]:
                keyname[key]=key
                form += "{"+key+":<"+str(min(length[key]+1,14))+"} "
            if tofile:
                with open(tofile, "a") as f:
                    f.write(form.format(**keyname)+"\n")
                    for row in d:
                        f.write(form.format(**row)+"\n")
                    f.write("\n")
            else:
                print(form.format(**keyname))
                for row in d:
                    print(form.format(**row))
                print("")



class kiddies:
    """
    KIDS wrapper for wmsapi
    generally easier to use, but fewer options

    wmsapi.kiddies(username, password [, target, goalnum])

    arguments:
    username -- username to log in to the wms interface
    password -- self explanatory
    target   -- target folder id to cycle KIDS images
    goalnum  -- number of images to cycle through

    kiddies.cyclekid(npath)
        to add a new image to cycle through

    kiddies.ping()
        pings the server, tests for valid login
    """

    def __init__(self, username, password, url="http://wms.viwetter.de/api/index.php", target=10, goalnum=2):
        self.api = wmsapi(username, password, url)
        self.target = target
        self.goal = goalnum

    def cyclekid(self, npath):
        """
        adds the file at <npath> to the default target, this object
        was initialized with.
        if more than self.goalnum images reside at self.target it deletes
        the oldest one after uploading
        """
        self.api.newCycle(npath,self.target)
        if self.api.getFolderSize(self.target) > self.goal:
            self.api.delLastCycle(self.target)

    def ping():
        """
        pings the server and return true if login data is correct
        """
        return self.api.ping()

def valid(url, username, password):
    """
    procedural version of wmsapi.ping(), tries to access the url and login
    returns true if server is on and accepts the login data
    be aware that you are sending your unencrypted password to the url

    arguments:
    url      -- php file to send the data to (needs to be the FILE*)
    username -- username to log in to the wms interface
    password -- self explanatory

    * doesn't work with \"http://wms.viwetter.de/api\" for example,
      it has to be \"http://wms.viwetter.de/api/index.php\" !
    """
    return "valid" == (requests.post(url, data={"username":username,"password":password,"function":"ping"})).text
