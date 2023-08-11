## ToDo:

* Split out mk-build-deps so user can see which dep is missing if it fails
* Check private repos are reachable
    * RUN apt-get update 2>&1 >/dev/null || (echo Fix Apt warning before progressing; exit 1)
* Allow user to specify apt priority for different repos
* Consider techiniques to speed up docker build. 
    * https://gist.github.com/reegnz/990d0b01b5f5e8670f78257875d8daa8
    * https://docs.docker.com/build/cache/
