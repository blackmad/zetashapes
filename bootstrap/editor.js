// TODO
// add recolor tool
// add paint tool
// add polygon tool
// add box tool
// actually call the api to get this
// actually call the api to send this
// ability to modify neighborhood names
// ability to change weightings
// move vote to a model

// server-side:
// filter out water
// add "smoothing" votes
// serve a list of candidates per areaid

var colors = [ "Aqua","Aquamarine","Bisque","Black","BlanchedAlmond","Blue","BlueViolet","Brown","BurlyWood","CadetBlue","Chartreuse","Chocolate","Coral","CornflowerBlue","Cornsilk","Crimson","Cyan","DarkBlue","DarkCyan","DarkGoldenRod","DarkGray","DarkGreen","DarkKhaki","DarkMagenta","DarkOliveGreen","Darkorange","DarkOrchid","DarkRed","DarkSalmon","DarkSeaGreen","DarkSlateBlue","DarkSlateGray","DarkTurquoise","DarkViolet","DeepPink","DeepSkyBlue","DimGray","DimGrey","DodgerBlue","FireBrick","ForestGreen","Fuchsia","Gainsboro","Gold","GoldenRod","Gray","Green","GreenYellow","HotPink","IndianRed","Indigo","Ivory","Khaki","Lavender","LavenderBlush","LawnGreen","LemonChiffon","LightBlue","LightCoral","LightCyan","LightGoldenRodYellow","LightGray","LightGreen","LightPink","LightSalmon","LightSeaGreen","LightSkyBlue","LightSlateGray","LightSteelBlue","Lime","LimeGreen","Linen","Magenta","Maroon","MediumAquaMarine","MediumBlue","MediumOrchid","MediumPurple","MediumSeaGreen","MediumSlateBlue","MediumSpringGreen","MediumTurquoise","MediumVioletRed","MidnightBlue","MistyRose","Moccasin","Navy","Olive","OliveDrab","Orange","OrangeRed","Orchid","PaleGoldenRod","PaleGreen","PaleTurquoise","PaleVioletRed","PapayaWhip","PeachPuff","Peru","Pink","Plum","PowderBlue","Purple","Red","RosyBrown","RoyalBlue","SaddleBrown","Salmon","SandyBrown","SeaGreen","Sienna","Silver","SkyBlue","SlateBlue","SlateGray","Snow","SpringGreen","SteelBlue","Tan","Teal","Thistle","Tomato","Turquoise","Violet","Wheat","Yellow","YellowGreen" ]

Array.prototype.remove = function(from, to) {
  var rest = this.slice((to || from) + 1 || this.length);
  this.length = from < 0 ? this.length + from : from;
  return this.push.apply(this, rest);
};

var MapPage = Backbone.View.extend({
  calculateBestVote: function(feature) {
    return _.max(feature.properties['votes'], function(v) { return v.count })
  },

  calculateBestLabel: function(feature) {
    var bestVote = this.calculateBestVote(feature)
    if (!bestVote) {
      return;
    }
    return bestVote.label;
  },

  calculateColor: function(feature) {
    var bestLabel = this.calculateBestLabel(feature);
    if (!bestLabel) {
      return;
    }
    var color = this.labelColors_[bestLabel];
    if (!color) {
      var randomnumber=Math.floor(Math.random()*colors.length)
      color = colors[randomnumber];
      this.labelColors_[bestLabel] = color;
      colors.remove(randomnumber);
    }
    return color;
  },

  setSelectedNeighborhood: function(id, label) {
    this.selectedNeighborhoodId_ = id
    this.selectedNeighborhoodLabel_ = label

    this.$selectedNeighborhoodSpan.text(label);
  },

  initialize: function() {
    this.inPaintMode_ = true;
    this.$selectedNeighborhoodSpan = $('#selectedNeighborhood');

    this.labelColors_ = {};
    console.log(this.options);
    if (this.options.geojson) {
      this.renderData(this.options.geojson);
    } else {
      this.fetchData(this.options.areaid);
    }
  },

  fetchData: function(areaid) {
    console.log('fetching ' + areaid)
    $.ajax({
      dataType: "json",
      url: "http://ubuntu-virtualbox.local:5000/citydata?callback=?",
      data: { areaid: '36061' },
      success: _.bind(this.renderData, this)
    })
  },

  colorFeature: function(feature, layer) {
    var popupContent = "id: " + feature.properties.id + " <br>label: " + this.calculateBestLabel(feature) + " <br>color: " + this.calculateColor(feature) +  "<br><br>";

    if (feature.properties) {
      popupContent += "<pre>" + JSON.stringify(feature.properties) + "</pre>";
    }

    layer.setStyle({
      weight: 1,
      color: this.calculateColor(feature),
      opacity: 1.0
    });
  },

  inPaintMode: function() {
    return this.inPaintMode_;
  },

  renderData: function(geojson) {
		var map = L.map('map', {dragging: true}).setView([40.74, -74], 13);
false
   	L.tileLayer('http://{s}.tile.cloudmade.com/{key}/22677/256/{z}/{x}/{y}.png', {
			attribution: 'Map data &copy; 2011 OpenStreetMap contributors, Imagery &copy; 2012 CloudMade',
			key: 'BC9A493B41014CAABB98F0471D759707'
		}).addTo(map);

    /* new L.tileLayer(
        'http://otile{s}.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png',
        {
          subdomains: '1234',
        }
      ).addTo(map); */

		function onEachFeature(feature, layer) {
      this.colorFeature(feature, layer); 
//			layer.bindPopup(popupContent);

      layer.on('mousedown', function(e) {
        console.log(e)
      });
     layer.on('click', function(e) {
        console.log(e)
      });

		}

		var geojsonLayer = L.geoJson([geojson], {
			style: function (feature) {
				return feature.properties && feature.properties.style;
			},

			onEachFeature: _.bind(onEachFeature, this)
		})
    
    geojsonLayer.addTo(map);

    geojsonLayer.on('contextmenu', _.bind(function(e) {
      console.log(e)
      var bestVote = this.calculateBestVote(e.layer.feature)
      this.setSelectedNeighborhood(bestVote.id, bestVote.label);
    }, this));
    
    geojsonLayer.on('click', function(e) {
      console.log(e)
    });

    geojsonLayer.on('mousedown', function(e) {
      console.log('mousedown')
      console.log(e)

          });

    map.on('dblclick',  _.bind(function(e) {
      if (this.inPaintMode()) {
        this.startedPainting_ = true
      }
    }, this));

    map.on('mousedown', _.bind(function(e) {
      console.log('mousedown')
      console.log(e)
  }, this));

    map.on('mouseup', _.bind(function(e) {
      console.log('mousedown')
      console.log(e)
      if (this.inPaintMode()) {
        this.startedPainting_ = false
      }

    }, this))


    geojsonLayer.on('mouseover', _.bind(function(e) {
      if (this.inPaintMode() && this.startedPainting_) {
        e.layer.feature.properties.votes.push({
          source: 'self',
          count: 10000,
          id: this.selectedNeighborhoodId_,
          label: this.selectedNeighborhoodLabel_
        });

    
      } else {
        e.layer.setStyle({
          weight: 1,
          color: 'red',
          opacity: 1.0
        });
      }
      this.currentFeatureHovered_ =  e.layer.feature;
    }, this));

    var mouseOutCb = function(e) {
      // console.log(e.layer.feature['properties']['id']);
      this.colorFeature(e.layer.feature, e.layer);
    }

    geojsonLayer.on('mouseout', _.bind(mouseOutCb, this))
  }
});
