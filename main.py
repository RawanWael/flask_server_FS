# Blue Print
import base64
import os
import secrets
import string
from tkinter import Image
import io
import json
import base64
import logging

import cv2
import jsonpickle as jsonpickle
import numpy as np

import flask
from fastapi.encoders import jsonable_encoder
from pymongo import ReturnDocument
from werkzeug.utils import secure_filename

import configurations
import json
import pymongo
from flask import *

# Models
from models.patient import Patient
from models.user import User
from models.user import UserLoginRequest
from models.therapist import Therapist
from models.exercise import Exercise
from models.appointment import Appointment
from models.perform import Perform
from models.session import Session

app = Flask(__name__)

# Testing to post an image
@app.route("/upload", methods=['POST'])
def dump_image():
    try:
        r = request
        # convert string of image data to uint8
        nparr = np.fromstring(r.data, np.uint8)
        # decode image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        cv2.imwrite("frame.png", img)

        # do some fancy processing here....

        # build a response dict to send back to client
        response = {'message': 'image received. size={}x{}'.format(img.shape[1], img.shape[0])
                    }
        # # encode response using jsonpickle
        response_pickled = jsonpickle.encode(response)
        #
        return Response(response=response_pickled, status=200, mimetype="application/json")
        return "WOW"
    except Exception as e:
        print(e)
        return "Already used username, try another one!"


# Pass the required route to the decorator.
# Login for any user (admin, patient, therapist)
# if returned_type = 0->admin, 1->therapist, 2->patient
@app.route("/login", methods=['POST'])
def login_user():
    try:
        # pass
        raw_user = request.get_json()
        user = UserLoginRequest(**raw_user)
        user_collection = pymongo.collection.Collection(configurations.db, 'User')
        db_user = user_collection.find_one({'_id': user.id})
        db_user = User(**db_user)
        print(db_user.password)
        if db_user.password == user.password:
            new_token = generate_new_token()
            user_collection.update_one({"_id": db_user.id}, {"$set": {"token": new_token}})
            return new_token
    except Exception as e:
        print(e)
        return "Already used username, try another one!"

def generate_new_token():
    N = 16
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                  for i in range(N))


# --------------------Admin------------------------#
# The admin can sign up a new therapist after passing the data through the request body
@app.route("/signup/therapist", methods=['POST'])
def signup_therapist():
    try:
        therapist_collection = pymongo.collection.Collection(configurations.db, 'Therapist')
        raw_therapist = request.get_json()
        therapist = Therapist(**raw_therapist)
        add_user(therapist.id, therapist.password, "1")
        therapist_collection.insert_one(therapist.to_bson())
        return therapist.to_json()
    except Exception as e:
        print(e)
        return "Already used username, try another one!"


# The admin can sign up a new patient after passing the data through the request body
@app.route("/signup/patient", methods=['POST'])
def signup_patient():
    try:
        patient_collection = pymongo.collection.Collection(configurations.db, 'Patient')
        raw_patient = request.get_json()
        patient = Patient(**raw_patient)
        add_user(patient.id, patient.password, "2")
        patient_collection.insert_one(patient.to_bson())
        return patient.to_json()
    except Exception as e:
        print(e)
        return "Already used username, try another one!"


def add_user(username, password, user_type):
    user_collection = pymongo.collection.Collection(configurations.db, 'User')
    passed_info = {'_id': username, 'password': password, 'user_type': user_type}
    user_collection.insert_one(passed_info)


# This API would get all the therapists based on the passed clinic id and the therapy type
# It will be used mainly in the signup of the patient, as we need a drop list with all possible therapist
@app.route("/therapistsByClinicIdAndTherapyType", methods=['GET'])
def therapists_clinic_id_therapy_type():
    token  = request.headers.get('Authorization')
    print(token)
    if authorization("333", token):
        info = json.loads(request.data)
        clinicId = info.get('clinicId', '')
        speciality = info.get('speciality', '')

        therapist_collection = pymongo.collection.Collection(configurations.db, 'Therapist')

        therapists = therapist_collection.find({'clinicId': clinicId, 'speciality': speciality})
        return [Therapist(**therapist).to_json() for therapist in therapists]
    return "Not Authorized"


# This API will get all patients based on the clinic ID
@app.route("/patientsByClinicId/<passed_id>", methods=['GET'])
def patients_clinic_id(passed_id):
    patient_collection = pymongo.collection.Collection(configurations.db, 'Patient')
    clinicId = passed_id
    patients = patient_collection.find({'clinicId': clinicId})
    return [Patient(**patient).to_json() for patient in patients]


# This API will update patient's data based on patient id
@app.route("/updatePatient/<passed_id>", methods=['PATCH'])
def update_patient(passed_id):
    patient_collection = pymongo.collection.Collection(configurations.db, 'Patient')
    patientId = passed_id
    updated_doc = patient_collection.update_one({"_id": patientId}, {"$set": request.get_json()})
    if updated_doc:
        return "updated"
    else:
        flask.abort(404, "Patient Not Found")


# This API will update therapist's data based on therapist id
@app.route("/updateTherapist/<passed_id>", methods=['PATCH'])
def update_therapist(passed_id):
    therapist_collection = pymongo.collection.Collection(configurations.db, 'Therapist')
    therapistId = passed_id
    updated_doc = therapist_collection.update_one({"_id": therapistId}, {"$set": request.get_json()})
    if updated_doc:
        return "updated"
    else:
        flask.abort(404, "Patient Not Found")


# This API will delete a patient based on its id
@app.route("/deletePatient/<passed_id>", methods=['DELETE'])
def delete_patient(passed_id):
    # delete from user collection
    user_collection = pymongo.collection.Collection(configurations.db, 'User')
    user_collection.delete_one({'_id': passed_id})
    # delete from therapist collection
    therapist_collection = pymongo.collection.Collection(configurations.db, 'Therapist')
    therapist_collection.update_many(
        {},
        {'$pull': {'patientId': passed_id}}
    )
    # delete from patient collection
    patient_collection = pymongo.collection.Collection(configurations.db, 'Patient')
    patient_collection.delete_one({'_id': passed_id})
    return "deleted"


# This API will delete a therapist based on its id
@app.route("/deleteTherapist/<passed_id>", methods=['DELETE'])
def delete_therapist(passed_id):
    # delete from user collection
    user_collection = pymongo.collection.Collection(configurations.db, 'User')
    user_collection.delete_one({'_id': passed_id})
    # delete from patient collection
    patient_collection = pymongo.collection.Collection(configurations.db, 'Patient')
    patient_collection.update_many(
        {},
        {'$pull': {'therapistId': passed_id}}
    )
    # delete from therapist collection
    therapist_collection = pymongo.collection.Collection(configurations.db, 'Therapist')
    therapist_collection.delete_one({'_id': passed_id})
    return "deleted"


# This API will get all patients for a specific therapist id
@app.route("/getPatientByTherapistId/<passed_id>", methods=['GET'])
def get_patient_by_therapist_id(passed_id):
    patient_collection = pymongo.collection.Collection(configurations.db, 'Patient')
    patients = patient_collection.find({'therapistId': passed_id})
    return [Patient(**patient).to_json() for patient in patients]


# This API will remove a specific patient from a specific therapist
@app.route("/deletePatientFromTherapist/<therapist_id>/<patient_id>", methods=['DELETE'])
def delete_patient_from_therapist(therapist_id, patient_id):
    # Remove from the patient id, the therapist id
    patient_collection = pymongo.collection.Collection(configurations.db, 'Patient')
    patient_collection.update_many(
        {'_id': patient_id},
        {'$pull': {'therapistId': therapist_id}}
    )
    # Remove from the therapist id, the patient id
    therapist_collection = pymongo.collection.Collection(configurations.db, 'Therapist')
    therapist_collection.update_many(
        {'_id': therapist_id},
        {'$pull': {'patientId': patient_id}}
    )
    return "deleted"


# This API will add a patient to a specific therapist
@app.route("/addPatientToTherapist/<therapist_id>/<patient_id>", methods=['PATCH'])
def add_patient_to_therapist(therapist_id, patient_id):
    # add the therapist to this patient
    patient_collection = pymongo.collection.Collection(configurations.db, 'Patient')
    patient_collection.update_many(
        {'_id': patient_id},
        {'$push': {'therapistId': therapist_id}}
    )
    # add the patient to the therapist's list
    therapist_collection = pymongo.collection.Collection(configurations.db, 'Therapist')
    therapist_collection.update_many(
        {'_id': therapist_id},
        {'$push': {'patientId': patient_id}}
    )
    return "Added"


# --------------------Patient------------------------#
# We are now in the Patient APIs according to the plan:
# This API gets all patient information based on the patient's id
@app.route("/patientInfo/<patient_id>", methods=['GET'])
def patient_information(patient_id):
    print("We are trying to get patient information\n")
    patient_collection = pymongo.collection.Collection(configurations.db, 'Patient')
    patient = patient_collection.find_one({'_id': patient_id})
    return Patient(**patient).to_json()


@app.route("/patientInfoAll", methods=['GET'])
def patient_information_all():
    patient_collection = pymongo.collection.Collection(configurations.db, 'Patient')
    patients = patient_collection.find()
    return [Patient(**patient).to_json() for patient in patients]



# This API will get Exercise information based on exerciseName
@app.route("/exerciseInformation/<exercise_name>", methods=['GET'])
def exercise_information(exercise_name):
    exercise_collection = pymongo.collection.Collection(configurations.db, 'Exercise')
    exercises = exercise_collection.find({'exerciseName': exercise_name})
    return [Exercise(**exercise).to_json() for exercise in exercises]


# This API will return the appointments for a specific patientId
@app.route("/patientAppointment", methods=['GET'])
def patient_appointment():
    appointment_collection = pymongo.collection.Collection(configurations.db, 'Appointment')
    info = json.loads(request.data)
    patient_id = info.get('patientId', '')
    appointment = appointment_collection.find({'patientId': patient_id})
    print(appointment)
    return [Appointment(**appointment).to_json() for appointment in appointment]


# This API will return the list of therpaists assigned for a specific patientId
@app.route("/getTherapistByPatientId//<patient_id>", methods=['GET'])
def get_therapist_by_patient_id(patient_id):
    therapist_collection = pymongo.collection.Collection(configurations.db, 'Therapist')
    therapists = therapist_collection.find({'patientId': patient_id})
    return [Therapist(**therapist).to_json() for therapist in therapists]


# This API will return the available appointment slots for a specific therapistId
@app.route("/getSlotsByTherapistId/<therapist_id>", methods=['GET'])
def get_slots_by_therapist_id(therapist_id):
    appointment_collection = pymongo.collection.Collection(configurations.db, 'Appointment')
    appointments = appointment_collection.find({'therapistId': therapist_id, 'status': 'available'})
    return [Appointment(**appointment).to_json() for appointment in appointments]


# This API will update appointment's status and add patientId based on appointment id
@app.route("/updateAppointmentStatusPending/<appointment_id>/<patient_id>", methods=['PATCH'])
def update_appointment_pending(appointment_id, patient_id):
    appointment_collection = pymongo.collection.Collection(configurations.db, 'Appointment')
    updated_doc = appointment_collection.update_one({"_id": appointment_id},
                                                    {"$set": {"patientId": patient_id, "status": "pending"}})
    if updated_doc:
        return "updated"
    else:
        flask.abort(404, "Patient Not Found")


# This API will add a new appointment by patient to be in the pending state
@app.route("/addPendingAppointment", methods=['POST'])
def add_pending_appointment():
    appointment_collection = pymongo.collection.Collection(configurations.db, 'Appointment')
    raw_appointment = request.get_json()
    appointment = Appointment(**raw_appointment)
    appointment_collection.insert_one(appointment.to_bson())
    return appointment.to_json()


# This API will get all the exercises that a patient should perform
@app.route("/getPerformsByPatientId/<patient_id>", methods=['GET'])
def get_performs_patient_id(patient_id):
    perform_collection = pymongo.collection.Collection(configurations.db, 'Performs')
    performs = perform_collection.find({'patientId': patient_id})
    return [Perform(**perform).to_json() for perform in performs]


# --------------------Therapist------------------------#
# This API will get Therapist information based on therapistId
@app.route("/therapistInformation/<therapist_id>", methods=['GET'])
def therapist_information(therapist_id):
    therapist_collection = pymongo.collection.Collection(configurations.db, 'Therapist')
    therapists = therapist_collection.find({'therapistId': therapist_id})
    return [Therapist(**therapist).to_json() for therapist in therapists]


# This API will return the list of patients assigned for a specific therapistId
@app.route("/getPatientsByTherapistId/<therapist_id>", methods=['GET'])
def get_patients_by_therapist_id(therapist_id):
    patient_collection = pymongo.collection.Collection(configurations.db, 'Patient')
    patients = patient_collection.find({'therapistId': therapist_id})
    return [Patient(**patient).to_json() for patient in patients]


# This API will return the list of performs assigned for a specific patientId by therapistId
@app.route("/getPerformsForPatientByTherapist/<therapist_id>/<patient_id>", methods=['GET'])
def get_performs_by_therapist_id_patient_id(therapist_id, patient_id):
    performs_collection = pymongo.collection.Collection(configurations.db, 'Performs')
    performs = performs_collection.find({'therapistId': therapist_id, 'patientId': patient_id})
    return [Perform(**perform).to_json() for perform in performs]


# This API will return the list of sessions of a specific exercise assigned by therapistId to a patientId
@app.route("/getSessionsByTherapistIdPatientIdExerciseName/<therapist_id>/<patient_id>/<exercise_name>", methods=['GET'])
def get_sessions_by_therapist_id_patient_id_exerciseName(therapist_id, patient_id, exercise_name):
    session_collection = pymongo.collection.Collection(configurations.db, 'Session')
    sessions = session_collection.find({'therapistId': therapist_id, 'patientId': patient_id, 'exerciseName': exercise_name})
    return [Session(**session).to_json() for session in sessions]


# This API will update session and add comment based on session_id
@app.route("/addCommentToSession/<session_id>", methods=['PATCH'])
def add_session_comment(session_id):
    session_collection = pymongo.collection.Collection(configurations.db, 'Session')
    updated_doc = session_collection.update_one({"_id": session_id}, {"$set": request.get_json()})
    if updated_doc:
        return "updated"
    else:
        return "error"


# This API will add a new perform to patientId by therapistId
@app.route("/addNewPerform", methods=['POST'])
def add_new_perform():
    try:
        performs_collection = pymongo.collection.Collection(configurations.db, 'Performs')
        info = json.loads(request.data)
        therapist_id = info.get('therapistId', '')
        patient_id = info.get('patientId', '')
        exercise_id = info.get('exerciseName', '')
        perform_id = therapist_id + "_" + patient_id + "_" + exercise_id
        raw_performs = request.get_json()
        perform = Perform(**raw_performs)
        perform.id = perform_id
        performs_collection.insert_one(perform.to_bson())
        return "true"
    except Exception as e:
        print(e)
        return "Error"


@app.route("/therapistAppointment", methods=['GET'])
def therapist_appointment():
    appointment_collection = pymongo.collection.Collection(configurations.db, 'Appointment')
    info = json.loads(request.data)
    therapist_id = info.get('therapistId', '')
    appointment = appointment_collection.find({'therapistId': therapist_id, 'status': "accepted"})
    print(appointment)
    return [Appointment(**appointment).to_json() for appointment in appointment]


# This API will return the pending appointments for a specific therapistId
@app.route("/therapistPendingAppointment", methods=['GET'])
def therapist_pending_appointment():
    appointment_collection = pymongo.collection.Collection(configurations.db, 'Appointment')
    info = json.loads(request.data)
    therapist_id = info.get('therapistId', '')
    appointment = appointment_collection.find({'therapistId': therapist_id, 'status': "pending"})
    print(appointment)
    return [Appointment(**appointment).to_json() for appointment in appointment]


# This API will update appointment status for a specific therapistId
@app.route("/updateAppointmentStatus/<appointment_id>", methods=['PATCH'])
def therapist_update_appointment(appointment_id):
    appointment_collection = pymongo.collection.Collection(configurations.db, 'Appointment')
    appointment = appointment_collection.update_one({'_id': appointment_id}, {"$set": request.get_json()})
    if appointment:
        return "updated"
    else:
        return "error"


# This API will return the exercises that can be added to a patient by the therapist without
# any duplication between these available exercises and the ones found in the performs
@app.route("/viewNewExercisesToAdd/<therapist_id>/<patient_id>", methods=['GET'])
def view_new_exercises_to_add(therapist_id, patient_id):
    # Three Steps:
    # 1- get the therapyType of the therapist,
    # 2- get exerciseId from performs by patientId and therapistId
    # 3- get exercises by therapyType, subtract those found in step 2
    # --------------------------- #
    therapist_collection = pymongo.collection.Collection(configurations.db, 'Therapist')
    therapist = therapist_collection.find_one({'_id': therapist_id})
    exerciseType = therapist['speciality']
    # --------------------------- #
    performs_collection = pymongo.collection.Collection(configurations.db, 'Performs')
    performs = performs_collection.find({'therapistId': therapist_id, 'patientId': patient_id})
    chosen_exercises = []
    for perform in performs:
        chosen_exercises.append(perform['exerciseName'])
    # --------------------------- #
    exercise_collection = pymongo.collection.Collection(configurations.db, 'Exercise')
    exercises = exercise_collection.find({'exerciseType': exerciseType})
    output_exercises = []
    print(chosen_exercises)
    print('---------------------------------------')
    for exercise in exercises:
        if exercise['exerciseName'] not in chosen_exercises:
            print(exercise['exerciseName'])
            output_exercises.append(exercise)

    return [Exercise(**exercise).to_json() for exercise in output_exercises]

    return ""


def authorization(id, token):
    user_collection = pymongo.collection.Collection(configurations.db, 'User')
    db_user = user_collection.find_one({'_id': id})
    db_user = User(**db_user)
    print(db_user.token)
    print(token)
    if 'Bearer '+db_user.token == token:
        print("YAY")
        return True
    return False


if __name__ == "__main__":
    app.run(host='0.0.0.0')
