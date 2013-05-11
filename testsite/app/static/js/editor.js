var colors = [ 'Aqua','Aquamarine','Bisque','Black','BlanchedAlmond','Blue','BlueViolet','Brown','BurlyWood','CadetBlue','Chartreuse','Chocolate','Coral','CornflowerBlue','Cornsilk','Crimson','Cyan','DarkBlue','DarkCyan','DarkGoldenRod','DarkGray','DarkGreen','DarkKhaki','DarkMagenta','DarkOliveGreen','Darkorange','DarkOrchid','DarkRed','DarkSalmon','DarkSeaGreen','DarkSlateBlue','DarkSlateGray','DarkTurquoise','DarkViolet','DeepPink','DeepSkyBlue','DimGray','DimGrey','DodgerBlue','FireBrick','ForestGreen','Fuchsia','Gainsboro','Gold','GoldenRod','Gray','Green','GreenYellow','HotPink','IndianRed','Indigo','Ivory','Khaki','Lavender','LavenderBlush','LawnGreen','LemonChiffon','LightBlue','LightCoral','LightCyan','LightGoldenRodYellow','LightGray','LightGreen','LightPink','LightSalmon','LightSeaGreen','LightSkyBlue','LightSlateGray','LightSteelBlue','Lime','LimeGreen','Linen','Magenta','Maroon','MediumAquaMarine','MediumBlue','MediumOrchid','MediumPurple','MediumSeaGreen','MediumSlateBlue','MediumSpringGreen','MediumTurquoise','MediumVioletRed','MidnightBlue','MistyRose','Moccasin','Navy','Olive','OliveDrab','Orange','OrangeRed','Orchid','PaleGoldenRod','PaleGreen','PaleTurquoise','PaleVioletRed','PapayaWhip','PeachPuff','Peru','Pink','Plum','PowderBlue','Purple','Red','RosyBrown','RoyalBlue','SaddleBrown','Salmon','SandyBrown','SeaGreen','Sienna','Silver','SkyBlue','SlateBlue','SlateGray','Snow','SpringGreen','SteelBlue','Tan','Teal','Thistle','Tomato','Turquoise','Violet','Wheat','Yellow','YellowGreen' ]

function cloneLatLng(ll) {
  return new L.LatLng(ll.lat, ll.lng);
};

var MapPage = Backbone.View.extend({
  recolorBlocks: function(blocks) {
    _.each(blocks, _.bind(function(block) {
      this.colorFeature(block.feature, block);
    }, this));

  },

  unhighlightPolygon: function() {
    if (this.currentPaintLine_) {
      this.map_.removeLayer(this.currentPaintLine_);
      this.recolorBlocks(this.lastHighlightedBlocks_);
      this.currentPaintLine_ = null;
    }
  },

  doVote: function(blockids, selectedHoodId) {
    _.each(blockids, _.bind(function(blockid) {
        this.idToLayerMap_[blockid].feature.properties['votes'].push(
        {
          count: 1,
          source: 'self',
          label: selectedHoodId
        })
      }, this)
    );

  // submit the votes
    $.ajax({
      dataType: 'json',
      url: '/api/vote',
      data: { 
        key: this.apiKey_,
        blockid: blockids.join(','),
        label: selectedHoodId
      },
      success: function() {
        window.console.log('your labels were successfully submitted');
      }
    })
  },

  getCurrentBlockIds: function() {
    var blockids = _.map(this.lastHighlightedBlocks_, function(f) {
      return f.feature['properties']['id'];
    });
    return blockids;
  },

  promptModal: function() {
    var idToLabelMap = {}
    var selectedIds = _.chain(this.lastHighlightedBlocks_)
      .map(function(e) {
        return _.map(e.feature.properties['votes'], function(f) {
          idToLabelMap[f['id']] = f['label'];
          return f['id'];
        })
      })
      .flatten()
      .uniq()
      .value()
    console.log(selectedIds);

    modalEl = $('#neighborhoodSelectModal')

    modalEl.on('show', function (e) {
      var select = $('.neighborhoodSelect');
      select.combobox();
    });

    modalEl.modal();

    var choicesEl = modalEl.find('.neighborhoodChoices')

    _.each(selectedIds, _.bind(function(id) {
      console.log(id);
      console.log(idToLabelMap);

      console.log(idToLabelMap[id]);
      var choiceDiv = $('<div class="choice"></div>');
      choicesEl.append(choiceDiv);
      $('<a>',{
        text: idToLabelMap[id],
        title: idToLabelMap[id],
        href: '#',
        click: _.bind(function() { 
          this.doVote(this.getCurrentBlockIds(), id);
          modalEl.modal('hide');
        }, this)
      }).appendTo(choiceDiv);
    }, this));

    modalEl.on('hidden', _.bind(function() {
      console.log('hidding!!!!');
      this.unhighlightPolygon();
    }, this));

    modalEl.find($('.closeButton')).on('click', function() {
      modalEl.modal('hide');
    });

    modalEl.find($('.saveButton')).on('click', _.bind(function() {
      console.log('save called');
      var selectedHoodId = $('.neighborhoodSelect').val();
      this.doVote(this.getCurrentBlockIds(), selectedHoodId);
 
      modalEl.modal('hide');
    }, this));
  },
    
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
      colors = _.without(colors, color)
    }
    return color;
  },

  setSelectedNeighborhood: function(id, label) {
    this.selectedNeighborhoodId_ = id
    this.selectedNeighborhoodLabel_ = label

    this.$selectedNeighborhoodSpan.text(label);
  },

  storeLabels: function(labelData) {
    this.labels_ = labelData['labels']; 
    var select = $('.neighborhoodSelect');

    // sort by name?
    _.each(this.labels_, function(label) {
      select.append($('<option>', { value: label['id'] }).text(label['label']));
    });
  },

  initialize: function() {
    this.idToLayerMap_ = {}
    this.inPolygonMode_ = false;
    this.$selectedNeighborhoodSpan = $('#selectedNeighborhood');

    this.labels_ = {};
    this.labelColors_ = {};
    this.apiKey_ = this.options.api_key;
    console.log(this.options);

    $.ajax({
      dataType: 'json',
      url: '/api/labels?callback=?',
      data: { areaid: this.options.areaid },
      success: _.bind(this.storeLabels, this)
    })

    if (this.options.geojson) {
      this.renderData(this.options.geojson);
    } else {
      this.fetchData(this.options.areaid);
    }
  },

  fetchData: function(areaid) {
    console.log('fetching ' + areaid)
    $.ajax({
      dataType: 'json',
      url: '/api/citydata?callback=?',
      data: {
        areaid: areaid,
        key: this.apiKey_,
      },
      success: _.bind(this.renderData, this)
    })
  },

  colorFeature: function(feature, layer) {
    var popupContent = 'id: ' + feature.properties.id + ' <br>label: ' + this.calculateBestLabel(feature) + ' <br>color: ' + this.calculateColor(feature) +  '<br><br>';

    if (feature.properties) {
      popupContent += '<pre>' + JSON.stringify(feature.properties) + '</pre>';
    }

    layer.setStyle({
      weight: 1,
      color: this.calculateColor(feature),
      opacity: 1.0
    });
  },

  inPolygonMode: function() {
    return this.inPolygonMode_;
  },

  highlightBlocks: function(blockIdsResponse) {
    this.recolorBlocks(this.lastHighlightedBlocks_);

    var blocks = _.chain(blockIdsResponse['ids'])
      .map(_.bind(function(id) {
          return this.idToLayerMap_[id];
        }, this))
      .compact()
      .value();

    this.lastHighlightedBlocks_ = blocks;
    
    _.each(blocks, _.bind(function(block) {
      block.setStyle({
          weight: 1,
          color: 'orange',
          opacity: 1.0
        });

    }, this))
  },

  highlightBlocksByGeometry: function(latlngs) {
    var lls = _.map(latlngs.concat([latlngs[0]]), function(ll) { return ll.lng + ' ' + ll.lat }).join(',')
    console.log('firing off highlight blocks')
    $.ajax({
      dataType: 'json',
      url: '/api/blocksByGeom?callback=?',
      data: { ll: lls },
      success: _.bind(this.highlightBlocks, this)
    })

  },

  processDoubleClick: function(e) { 
    console.log('dblclick')
    console.log(e)
    if (this.inPolygonMode()) {
      console.log('in paint mode')
      if (this.currentPaintLine_) {
        this.highlightBlocksByGeometry(this.currentPaintLine_.getLatLngs())
        this.promptModal();
      }
    } 
    L.DomEvent.stopPropagation(e);
  },

  clearSelection: function() {
    
  },

  processClick: function(e) { 
    console.log('click')
    console.log(e)
    if (this.inPolygonMode()) {
      console.log('in paint mode')
      if (this.currentPaintLine_) {
        var lastIndex = this.currentPaintLine_.getLatLngs().length - 1
        console.log(this.currentPaintLine_.getLatLngs()[0].distanceTo(e.latlng));
        if (this.currentPaintLine_.getLatLngs()[0].distanceTo(e.latlng) < 100) {
          this.highlightBlocksByGeometry(this.currentPaintLine_.getLatLngs())
          this.currentPaintLine_ = null;
        } else {
          this.highlightBlocksByGeometry(this.currentPaintLine_.getLatLngs())
          this.currentPaintLine_.spliceLatLngs(lastIndex, 1, cloneLatLng(e.latlng), cloneLatLng(e.latlng));
        }
      } else {
        this.lastHighlightedBlocks_ = [];
        this.currentPaintLine_ = new L.Polygon([cloneLatLng(e.latlng), cloneLatLng(e.latlng)]);
        this.map_.addLayer(this.currentPaintLine_);
      }
    } else {
      this.promptModal()
    } 
    L.DomEvent.stopPropagation(e);
  },

  togglePolygonMode: function() {
    this.inPolygonMode_ = !this.inPolygonMode_;
  },

  renderData: function(geojson) {
	var map = L.map('map', {dragging: true}).setView([40.74, -74], 13);
    this.$polygonMode = $('#polygonMode')
    this.$polygonMode.button();
    this.$polygonMode.click(_.bind(this.togglePolygonMode, this))

    this.map_ = map;
    this.map_.doubleClickZoom.disable(); 
   	L.tileLayer('http://{s}.tile.cloudmade.com/{key}/22677/256/{z}/{x}/{y}.png', {
			attribution: 'Map data &copy; 2011 OpenStreetMap contributors, Imagery &copy; 2012 CloudMade',
			key: 'BC9A493B41014CAABB98F0471D759707'
		}).addTo(map);

    this.lastHighlightedBlocks_ = [];

    /* new L.tileLayer(
        'http://otile{s}.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png',
        {
          subdomains: '1234',
        }
      ).addTo(map); */

    var centered = false;
    function onEachFeature(feature, layer) {
      if (!centered) {
        window.console.log(feature);
        map.panTo(new L.LatLng(feature.geometry.coordinates[0][0][0][1], feature.geometry.coordinates[0][0][0][0]));
        centered = true;
      } 
      this.idToLayerMap_[feature.properties.id] = layer
      this.colorFeature(feature, layer); 
//			layer.bindPopup(popupContent);

      /*layer.on('mousedown', function(e) {
        console.log(e)
      }); */
		}

		var geojsonLayer = L.geoJson([geojson], {
			style: function (feature) {
				return feature.properties && feature.properties.style;
			},

			onEachFeature: _.bind(onEachFeature, this)
		})
    
    geojsonLayer.addTo(map);
 
    map.on('click', _.bind(this.processClick, this))
    map.on('dblclick', _.bind(this.processDoubleClick, this))
    geojsonLayer.on('click', _.bind(this.processClick, this))

    map.on('mousemove', _.bind(function(e) {
        // console.log(e)
        if (this.inPolygonMode()) {
          if (this.currentPaintLine_) {
            var lastIndex = this.currentPaintLine_.getLatLngs().length - 1
            this.currentPaintLine_.spliceLatLngs(lastIndex, 1, cloneLatLng(e.latlng));
          }
        } 
      }, this));

    /*geojsonLayer.on('contextmenu', _.bind(function(e) {
      console.log(e)
      var bestVote = this.calculateBestVote(e.layer.feature)
      this.setSelectedNeighborhood(bestVote.id, bestVote.label);
    }, this));*/
    
    /*geojsonLayer.on('click', function(e) {
      console.log(e)
    });

    geojsonLayer.on('mousedown', function(e) {
      console.log('mousedown')
      console.log(e)

          });

    map.on('dblclick',  _.bind(function(e) {
      if (this.inPolygonMode()) {
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
      if (this.inPolygonMode()) {
        this.startedPainting_ = false
      }

    }, this))
    */


    geojsonLayer.on('mouseover', _.bind(function(e) {
      e.layer.setStyle({
        weight: 1,
        color: 'red',
        opacity: 1.0
      });
      
      if (!this.inPolygonMode()) {
        this.lastHighlightedBlocks_ = [ e.layer ];
      }  

      $('#neighborhoodInfo').html(
        'id<br>' +
        e.layer.feature.properties.id +
        '<br>label<br>' +
        this.calculateBestLabel(e.layer.feature)
      );
    }, this));

    var mouseOutCb = function(e) {
      // console.log(e.layer.feature['properties']['id']);
      this.colorFeature(e.layer.feature, e.layer);
    }

    geojsonLayer.on('mouseout', _.bind(mouseOutCb, this))
  }
});
