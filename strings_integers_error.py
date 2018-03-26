error!!!!
Traceback (most recent call last):
  File "grading-assigner.py", line 317, in run_main
    request_reviews()
  File "grading-assigner.py", line 172, in request_reviews
    wait_for_assign_eligible(current_request)
  File "grading-assigner.py", line 93, in wait_for_assign_eligible
    get_wait_stats()
  File "grading-assigner.py", line 278, in get_wait_stats
    proj_name = proj_id_dict[int(p['project_id'])]
TypeError: string indices must be integers
From: Udacity.Review.Notifications@gmail.com
To: nathancgeorge@gmail.com
Subject: Error on Udacity server: string indices must be integers
Error: string indices must be integers
Traceback (most recent call last):
  File "grading-assigner.py", line 317, in run_main
    request_reviews()
  File "grading-assigner.py", line 172, in request_reviews
    wait_for_assign_eligible(current_request)
  File "grading-assigner.py", line 93, in wait_for_assign_eligible
    get_wait_stats()
  File "grading-assigner.py", line 278, in get_wait_stats
    proj_name = proj_id_dict[int(p['project_id'])]
TypeError: string indices must be integers
2018-03-26 09:44:06.620798-06:00
