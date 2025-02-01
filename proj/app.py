@app.route("/fibonacci", methods=["GET"])
def fibonacci_num():
    seq = [0, 1]
    for i in range(8):
        seq.append(seq[-1] + seq[-2])
    return jsonify(sequence=seq)