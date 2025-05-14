# Exercise: How to Parse Big Data in Memory Within Multiple Processes Without Blocking

1. Install dependencies: `pip install -r req.txt`
2. Deploy and configure MinIO to emulate an S3 service
3. Generate `big_data.json` and upload it to MinIO
4. Copy `config.example.py` to `config.py` and set the proper values
5. Run the program with `python run.py` and enjoy
6. Subprocess is not exiting correctly on keyboard interrupt. So use command below to stop service

    ```shell
    kill -9 $(ps aux | grep "python run.py" | grep -v grep | awk '{print$2}')
    ```
