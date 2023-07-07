from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB Configuration
MONGO_URI = 'mongodb://localhost:27017'  # Update with your MongoDB connection URI
DATABASE = 'your_database_name'  # Update with your database name
USER_COLLECTION = 'users'  # Collection to store user data

# Connect to MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DATABASE]
users_collection = db[USER_COLLECTION]


@app.route('/', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        # User already logged in, redirect to file upload page
        return redirect('/upload')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({'email': email, 'password': password})
        if user:
            # Successful login, set the session and redirect to file upload page
            session['email'] = email
            return redirect('/upload')
        else:
            # Handle login error
            return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Check if the email already exists in the database
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            # Handle signup error
            return render_template('signup.html', error='Email already exists')
        else:
            # Create a new user document
            new_user = {'email': email, 'password': password}
            # Insert the new user document into the database
            users_collection.insert_one(new_user)
            # Successful signup, set the session and redirect to file upload page
            session['email'] = email
            return redirect('/upload')
    return render_template('signup.html')


import os


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        file.save(f'uploads/{file.filename}')

    # Get the list of uploaded files
    files = os.listdir('uploads')

    return render_template('upload.html', files=files)


@app.route('/logout')
def logout():
    # Clear the session and redirect to login page
    session.pop('email', None)
    return redirect('/')


@app.route('/download/<filename>')
def download(filename):
    return send_from_directory('uploads', filename)

@app.route('/calculate_sha256', methods=['POST'])
def calculate_sha256():
    file_content = request.files['file'].read()

    # Save the file
    with open('uploaded_file', 'wb') as file:
        file.write(file_content)

    # Execute the chaincode
    command = 'peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile "${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem" -C mychannel -n basic --peerAddresses localhost:7051 --tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt" --peerAddresses localhost:9051 --tlsRootCertFiles "${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt" -c \'{"function":"CalculateSHA256","Args":[]}\''  # Modify with the appropriate chaincode invocation command

    try:
        output = subprocess.check_output(command, shell=True)
        sha256 = output.decode().strip()
        return jsonify({'sha256': sha256})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run()
