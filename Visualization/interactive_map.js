    var color_dict = {1: '#274c79', 2: '#f79051', 3: '#c10002', 4: '#703e62'};
    var map = L.map('map').setView([59.9139, 10.7522], 13);

    L.tileLayer('https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var request = new XMLHttpRequest();
    request.open("GET", "station_vis.json", false);
    request.send(null);

    var station_json = JSON.parse(request.responseText);
    var station_dict = {};

    for (var key in station_json) {
        if (station_json.hasOwnProperty(key)) {
            // [lat, long], charged bikes, flat bikes, starvations, congestions, cap, depot
            station_dict[key] = [station_json[key][0], station_json[key][1], station_json[key][2],
                station_json[key][3], station_json[key][4], station_json[key][5], station_json[key][6]];
        }
    }

    var request_vehicle = new XMLHttpRequest();
    request_vehicle.open("GET", "vehicle.json", false);
    request_vehicle.send(null);

    var vehicle_json = JSON.parse(request_vehicle.responseText);

    for (var id in station_dict) {
        if (station_dict.hasOwnProperty(id)) {
            var popup_msg = 'Station ID: ' +  id + ', Cap: ' + String(station_dict[id][5]) + ', ' +
                String(station_dict[id][1]) + ' charged bikes, '
                + String(station_dict[id][2]) +  ' flat bikes';
            var edge_col = color_dict[1];
            if (station_dict[id][3] > 0) {
                edge_col = color_dict[2]
            } if (station_dict[id][3] > 20) {
                edge_col = color_dict[3]
            }

            var fill_col = color_dict[1];
            if (station_dict[id][6] > 0) {
                fill_col = color_dict[4]
            } else if (station_dict[id][4] > 20) {
                fill_col = color_dict[3]
            } else if (station_dict[id][4] > 0) {
                fill_col = color_dict[2]
            }

            var station = L.circle(station_dict[id][0], {
                color: edge_col,
                fillColor: fill_col,
                fillOpacity: 0.7,
                radius: 50
            }).bindPopup(popup_msg).addTo(map);
        }
    }

    var car = L.icon({
        iconUrl: 'service_vehicle.png',
        iconSize: [45, 30]
    });

    var stop = L.icon({
        iconUrl: 'service_stop.png',
        iconSize: [20, 15]
    });

    for (var car_id in vehicle_json) {
        // q_B, q_CCL, q_FCL, q_CCU, q_FCU
        if (vehicle_json.hasOwnProperty(car_id)) {
            console.log(vehicle_json[car_id][1].length);
            for (var j = 0; j < vehicle_json[car_id][1].length; j++) {
            var popup = ' STOP ' + String(j+1) + ', Car ID: ' + car_id + ', ' + String(vehicle_json[car_id][1][j][0]) + ' charged bikes, '+
                String(vehicle_json[car_id][1][j][1]) + ' flat bikes, ' + String(vehicle_json[car_id][1][j][2]) + ' batteries' +
                ' Battery swaps: ' + String(vehicle_json[car_id][2][j][0]) + ', Charged loaded: ' + String(vehicle_json[car_id][2][j][1])
            + ', Flat loaded: ' + String(vehicle_json[car_id][2][j][2]) + ', Charged unloaded: ' + String(vehicle_json[car_id][2][j][3])
            + ', Flat unloaded: ' + String(vehicle_json[car_id][2][j][4] + ', Station inventory at visit: Charged ' +
                String(vehicle_json[car_id][3][j][0]) + ', Flat: ' + String(vehicle_json[car_id][3][j][1]));
            if (j == (vehicle_json[car_id][1].length - 1)) {
                L.marker(station_dict[vehicle_json[car_id][0][j]][0], {icon: car}).addTo(map).bindPopup(popup).addTo(map);
            } else {
                L.marker(station_dict[vehicle_json[car_id][0][j]][0], {icon: stop}).addTo(map).bindPopup(popup).addTo(map);
            }
            }
            for (k = 0; k < vehicle_json[car_id][0].length - 1; k++) {
                var polyline = L.polyline([station_dict[vehicle_json[car_id][0][k]][0],
                        station_dict[vehicle_json[car_id][0][k+1]][0]],
                    {color: color_dict[parseInt(car_id)+1]}).addTo(map);
            }
        }
    }
