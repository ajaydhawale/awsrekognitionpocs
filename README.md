This is a poc to explore Amazon's Rekognition, more specifically using its face detection feature. Voting is simulated by way of detecting smile in an uploaded selfie. If Rekognition returns 'Happy' with confidence score over 60.00, the sentiment is marked as happy, else unhappy.

#### Pre-requisites (versions using which code is tested):
* Python: v2.7.12
* Python Packages:
    * boto3 (1.4.7): AWS Python SDK
    * PIL (1.1.6): Python Imaging Library
* OS: Ubuntu 16.04
* Web server: apache2
* Access to AWS Rekognition

#### Files:
Place
* process_sentiments.py in cgi-bin directory
* vote.html in a directory that is accessible via web server
* config.ini as appropriate (in the poc vote.html and config.ini were kept in document root)

#### Note:
The user under which web server is running should have
* Read access to AWS Configuration and Credential Files (refer: http://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html)
* Read and write permissions on SENTIMENTS_DIRECTORY
