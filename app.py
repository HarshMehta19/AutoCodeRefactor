from flask import Flask, jsonify, request
from joblib import load
from transformers import T5ForConditionalGeneration, T5Tokenizer
import requests
from flask import Flask, render_template, request, jsonify
import json
import numpy as np
import os
import processing
app = Flask(__name__)

# @app.route('/')
# def home():
#     model = T5ForConditionalGeneration.from_pretrained('M:\Data\Dal\Term2\ML\magic_smell_model_s_13000_e15_b4')

#     tokenizer = T5Tokenizer.from_pretrained('t5-small')

#     # Step 2: Preprocess Input (Assuming X_test is your input data)
#     # X_test = preprocess_input(X_test)

#     # Step 3: Generate Predictions
    # test = """        CheckedOutputStream crcOut = new CheckedOutputStream(sessOS, new Adler32());a
    #     //CheckedOutputStream cout = new CheckedOutputStream()
    #     OutputArchive oa = BinaryOutputArchive.getArchive(crcOut);
    #     FileHeader header = new FileHeader(SNAP_MAGIC, 2, dbId);
    #     serialize(dt,sessions,oa, header);
    #     long val = crcOut.getChecksum().getValue();
    #     oa.writeLong(val, "val");"""
    
    
#     ids = tokenizer(test, return_tensors='pt').input_ids
#     result = model.generate(ids, max_length=1000, num_beams=5, no_repeat_ngram_size=2, early_stopping=True)
#     predictions = tokenizer.decode(result[0], skip_special_tokens=True)
#     # predictions = model.predict(test)

#     # Step 4: Postprocess Output if necessary
#     # predictions = postprocess_output(predictions)

#     # Print or use predictions
#     print(predictions)
#     return predictions

@app.route('/')
def index():
    # file_name = "input_code.java"
    # file_path = os.path.join("input", file_name)
    # result_path = os.path.join("output")
    # line_no = processing.check_smell(result_path, "Magic Number")
    # print("line_no: ", line_no)
    # result = processing.extract_lines_around_line(file_path, line_no, 3, 3)
    # print("result: ", result)
    return render_template('index.html')

# create a post method that accept the code as input in header and pass it to the self deployed hugging face model and return the output generated by the model

@app.route('/refactor', methods=['POST'])
def refactor():
    code = request.headers.get('code')
    if not code:
        return jsonify({'error': 'No code provided in the header'}), 400

    # Call your self-deployed Hugging Face model API
    model_endpoint = 'YOUR_MODEL_ENDPOINT_HERE'
    headers = {'Authorization': 'Bearer YOUR_API_TOKEN_HERE'}
    payload = {'code': code}

    try:
        response = requests.post(model_endpoint, headers=headers, json=payload)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to refactor code'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# @app.route('/process_code', methods=['POST'])
# def process_code():
#     code = request.form['code']
#     model = T5ForConditionalGeneration.from_pretrained('M:\Data\Dal\Term2\ML\magic_smell_model_s_13000_e15_b4')

#     tokenizer = T5Tokenizer.from_pretrained('t5-small')

#     ids = tokenizer(code, return_tensors='pt').input_ids
#     result = model.generate(ids, max_length=200, num_beams=5, no_repeat_ngram_size=2, early_stopping=True)
#     predictions = tokenizer.decode(result[0], skip_special_tokens=True)
#     print(predictions)
#     return jsonify({'processed_code': predictions})
    
@app.route('/process_code', methods=['POST'])
def process_code():
    code = request.form['code']
    
    # Use the model hosted on Hugging Face
    # model = T5ForConditionalGeneration.from_pretrained('t5-small')
    # tokenizer = T5Tokenizer.from_pretrained('t5-small')
    # tokenizer.save_pretrained("M:\Data\Dal\Term2\ML\Project\huggingface-models")

    # input_ids = tokenizer(code, return_tensors='pt').input_ids
    

    API_URL = "https://api-inference.huggingface.co/models/harsh-mehta19/test-magic-number"
    headers = {"Authorization": "Bearer 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"}

    file_name = "input_code.java"
    folder_path = os.path.join("input")
    file_path = os.path.join("input", file_name)
    result_path = os.path.join("output")
    DJ_path = os.path.join("DJ", 'DesigniteJava.jar')
    with open(file_path, 'w') as file:
        file.write(code)
    processing.analyze_code(folder_path, result_path, os.path.abspath(DJ_path))

    line_no, value = processing.check_smell(result_path, "Magic Number")

    print("line_no: ", line_no)
    print("value: ", value)

    final_line_no = processing.find_number_below_line(file_path, line_no, value)
    if final_line_no == -1:
        print("No magic number found in the code")
        return jsonify({'processed_code': "No magic number found in the code"})
    print("final_line_no: ", final_line_no)
    selected_code = processing.extract_lines_around_line(file_path, final_line_no, 3, 3)

    # print("selected_code: ", selected_code)

    payload = {
        "inputs": selected_code,
        'max_length': 500,
        "wait_for_model": True,
        "use_cache": False,
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    json_string = response.content

    response_json = json.loads(json_string.decode('utf-8'))
    print("json_string: ", response_json)
    response_content = response_json[0]['generated_text']
    declartion_of_variable = processing.get_first_line(response_content)
    print("declartion_of_variable: ", declartion_of_variable)
    if declartion_of_variable is None:
        return jsonify({'processed_code': response_content + "\n\n Inference API token_length exceeded"})
    # variable_name = processing.get_variable_name(declartion_of_variable)
    variable_name = processing.extract_variable_name(declartion_of_variable)
    final_result = processing.replace_number_with_variable(code, final_line_no, value, variable_name)
    print("content: ", final_result)


    print("variable_name: ", variable_name)
        # response_content = response_content.replace(declartion_of_variable, "")
    processing.delete_files(folder_path)
    processing.delete_files(result_path)
	
    return jsonify({'processed_code': final_result, 'declaration_variable': declartion_of_variable, 'result': 'Magic Number refactored successfully!'})


if __name__ == '__main__':
    app.run(debug=True)