$(function() {
    // Set
    var main = $('div.mm-dropdown .textfirst')
    var li = $('div.mm-dropdown > ul > li.input-option')
    var inputoption = $("div.mm-dropdown .option")
    var default_text = 'Select<img src="https://cdn4.iconfinder.com/data/icons/ionicons/512/icon-arrow-down-b-128.png" width="10" height="10" class="down" />';

    // Animation
    main.click(function() {
        main.html(default_text);
        li.toggle('fast');
    });

    // Insert Data
    li.click(function() {
        // hide
        li.toggle('fast');
        var livalue = $(this).data('value');
        var lihtml = $(this).html();
        main.html(lihtml);
        inputoption.val(livalue);
    });
});





function togglePickupTime() {
    var timeSelection = document.getElementById("time-selection");
    var pickupTimeInput = document.getElementById("pickup-time");

    if (timeSelection.value === "later") {
      pickupTimeInput.style.display = "block"; 
    } else {
      pickupTimeInput.style.display = "none"; 
    }
}






function calculateDistanceAndDisplay() {
    const pickupLocation = document.getElementById('pickup-input').value;
    const dropoffLocation = document.getElementById('dropoff-input').value;
  
    // Initialize Distance Matrix Service
    const distanceMatrixService = new google.maps.DistanceMatrixService();
  
    distanceMatrixService.getDistanceMatrix({
      origins: [pickupLocation],
      destinations: [dropoffLocation],
      travelMode: google.maps.TravelMode.DRIVING,
      unitSystem: google.maps.UnitSystem.METRIC, // Use METRIC for kilometers
    }, function(response, status) {
      if (status === 'OK') {
        const distanceText = response.rows[0].elements[0].distance.text;
  
        // Update distance for each ride recommendation
        const rideElements = document.querySelectorAll('.ride-recommendations .ride');
        rideElements.forEach(function(rideElement) {
          const distanceParagraph = rideElement.querySelector('p:last-of-type');
          if (distanceParagraph) {
            distanceParagraph.textContent = `Distance: ${distanceText}`;
          }
        });
      } else {
        alert('Error occurred while calculating distance: ' + status);
      }
    });
  }






let map;
    let geocoder;

    function initMap() {
      // Initialize map
      map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: 40.7128, lng: -74.0060 },
        zoom: 12
      });

      // Initialize Geocoder
      geocoder = new google.maps.Geocoder();

        // Initialize PlacesService for autocomplete
        placesService = new google.maps.places.Autocomplete(document.getElementById('pickup-input'));
      placesService.bindTo('bounds', map);

      placesService = new google.maps.places.Autocomplete(document.getElementById('dropoff-input'));
      placesService.bindTo('bounds', map);
      
    }

    function showLocations() {
      const pickupLocation = document.getElementById('pickup-input').value;
      const dropoffLocation = document.getElementById('dropoff-input').value;
      var mapElement = document.getElementById("map");
      

  // Check if the map element exists
      if (mapElement) {
        // Change the width of the map element to 40%
        mapElement.style.width = "25%";
      }

      var rideRecommendations = document.querySelector('.ride-recommendations');

// Check if rideRecommendations element exists
if (rideRecommendations) {
  // Change display to block when search button is clicked
  rideRecommendations.style.display = "block";
}
      

      geocodeAddress(pickupLocation, 'Pickup', function(pickupLatLng) {
        geocodeAddress(dropoffLocation, 'Dropoff', function(dropoffLatLng) {
          displayDirections(pickupLatLng, dropoffLatLng);
          calculateDistanceAndDisplay();
        });
      });
    }

    function displayDirections(pickupLatLng, dropoffLatLng) {
  const directionsService = new google.maps.DirectionsService();
  const directionsRenderer = new google.maps.DirectionsRenderer({
    map: map,
    suppressMarkers: true, 
    polylineOptions: {
      strokeColor: 'black', 
      strokeOpacity: 1.0,
      strokeWeight: 6
    }
  });

  const request = {
    origin: pickupLatLng,
    destination: dropoffLatLng,
    travelMode: google.maps.TravelMode.DRIVING
  };

  directionsService.route(request, function(response, status) {
    if (status === 'OK') {
      directionsRenderer.setDirections(response);
    } else {
      alert('Directions request failed due to ' + status);
    }
  });
}



function geocodeAddress(location, type, callback) {
  geocoder.geocode({ address: location }, function(results, status) {
    if (status === 'OK') {
      const loc = results[0].geometry.location;

      if (type === 'Pickup') {
        const svgPath = `M-.035 10.794h8.36v-1.8c.001-.331.27-.599.602-.599h6.015c.335 0 .602.268.602.6v6c0 .331-.269.599-.601.6h-6.018c-.331-.001-.6-.269-.6-.599v-.001-1.8h-8.359c.665 6.595 6.562 11.402 13.172 10.74 6.611-.663 11.43-6.546 10.765-13.14-.631-6.091-5.748-10.8-11.967-10.8h-.001c-6.22 0-11.338 4.709-11.966 10.748z`;

        const iconUrl = {
          path: svgPath,
          fillColor: 'black',
          fillOpacity: 1,
          strokeWeight: 0,
          scale: 1,
          anchor: new google.maps.Point(0, 0)
        };

        new google.maps.Marker({
          position: loc,
          map: map,
          title: type + ' Location',
          icon: iconUrl,
          optimized: false
        });

        map.setCenter(loc);
        callback(loc);
      } else if (type === 'Dropoff') {
        const dropoffSvg = `
          <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-map-pin">
            <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
            <circle cx="12" cy="10" r="3"/>
          </svg>
        `;

        const dropoffIcon = {
          url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(dropoffSvg),
          scaledSize: new google.maps.Size(36, 36), // Adjust the size of the icon if needed
          anchor: new google.maps.Point(18, 36) // Adjust the anchor point if needed
        };

        new google.maps.Marker({
          position: loc,
          map: map,
          title: type + ' Location',
          icon: dropoffIcon
        });

        callback(loc);
      }
    } else {
      alert('Both fields are required, please try again!');
    }
  });
}







let carRide = ''; // Define a global variable to store the selected ride

function storeSelectedRide(radioButton) {
    carRide = radioButton.value;
}
function storeUserData() {
  const pickupLocation = document.getElementById('pickup-input').value;
  const dropoffLocation = document.getElementById('dropoff-input').value;
  const pickupTime = document.getElementById('pickup-time').value;
  const paymentMethod = document.querySelector('.mm-dropdown .textfirst').textContent.trim();

  const userData = {
    pickup_location: pickupLocation,
    dropoff_location: dropoffLocation,
    pickup_time: pickupTime,
    payment_method: paymentMethod,
    car_ride: carRide
  };

  fetch('/save_data', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(userData)
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      console.log('Success:', data);
      const order_id = data.order_id; // Extract the order_id from the response

  // Redirect to the waiting page with the received order_id in the URL
      window.location.href = `/waiting/${order_id}`;
      
    })
    .catch(error => {
      console.error('Error:', error);
      // Handle errors if needed
    });
}







