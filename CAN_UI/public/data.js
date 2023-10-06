const components = [
    {
        "pgn" : "0x925",
        "Name": "Lights",
        "title": "Sample Konfabulator Widget",
        "name": "main_window",
        "instances": [{"name": "Bath", "id": 1}, {"name": "Bed", "id": 2}, {"name": "Porch", "id": 3}, {"name": "Service", "id": 4}],
        "width": 500,
        "height": 500,
        "id" : 1
    },
    {   
        "pgn" : "0x928",
        "Name": "Furnance", 
        "src": "Images/Sun.png",
        "name": "sun1",
        "instances": [{"name": "Black Water", "id": 1}],
        "hOffset": 250,
        "vOffset": 250,
        "alignment": "center",
        "id" : 2
    },
    {   "pgn" : "0x924",
        "Name":"AC", 
        "data": "Click Here",
        "size": 36,
        "style": "bold",
        "name": "text1",
        "instances": [{"name": "Truma", "id": 1}],
        "hOffset": 250,
        "vOffset": 100,
        "alignment": "center",
        "onMouseUp": "sun1.opacity = (sun1.opacity / 100) * 90;",
        "id" : 3
    },
    {   "pgn" : "0x935",
        "Name": "Sensor1",
        "title": "Sample Konfabulator Widget",
        "name": "main_window",
        "instances": [{"name": "ter", "id": 1}],
        "width": 500,
        "height": 500,
        "id" : 4
    },
    {   
        "pgn" : "0x995",
        "Name": "Sensor2",  
        "src": "Images/Sun.png",
        "name": "sun1",
        "instances": [{"name": "Bl", "id": 1}],
        "hOffset": 250,
        "vOffset": 250,
        "alignment": "center",
        "id" : 5
    },
    {   
        "pgn" : "0x625",
        "Name": "BMS", 
        "data": "Click Here",
        "size": 36,
        "instances": [{"name": "BMS", "id": 1}],
        "style": "bold",
        "name": "text1",
        "hOffset": 250,
        "vOffset": 100,
        "alignment": "center",
        "onMouseUp": "sun1.opacity = (sun1.opacity / 100) * 90;",
        "id" : 6
    },
    {   "pgn" : "0x125",
        "Name": "Fluids",
        "data": "Click Here",
        "instances": [{"name": "Black Water", "id": 1},{"name": "Grey Water", "id": 2},{"name": "Fresh Water", "id": 3}],
        "style": "bold",
        "name": "text1",
        "hOffset": 250,
        "vOffset": 100,
        "alignment": "center",
        "onMouseUp": "sun1.opacity = (sun1.opacity / 100) * 90;",
        "id" : 7
    }
]

export default components