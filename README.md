# udacity_review_assigner
Automatically assigns Udacity reviews; sends text alerts; tracks stats in DB.

This was originally a fork from [here](https://github.com/udacity/grading-assigner).

# Getting started
I run this on AWS.
You need to install mongodb, then start it with

`sudo mongod --dbpath=/var/lib/mongodb --smallfiles`

After creating a backup of the drive without shutting down, mongodb was locked and wouldn't run.  I had to [repair the db](https://stackoverflow.com/questions/9953295/how-to-repair-my-mongodb).  Basically, I did:

```bash
$ mongo
> use udacity_reviews
> db.repairDatabase()
```

and it took a decent amount of time.  Next time, be sure to shut down everything before backing up the drive.
