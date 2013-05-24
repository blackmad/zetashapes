// when done, submit positive and negative votes
// be able to register negative votes
// wait for block data

// figure out something to do about brookln piers

var originalColors = [ 'Aqua','Aquamarine','BlanchedAlmond','Blue','BlueViolet','Brown','BurlyWood','CadetBlue','Chartreuse','Chocolate','Coral','CornflowerBlue','Cornsilk','Crimson','Cyan','DarkBlue','DarkCyan','DarkGoldenRod','DarkGray','DarkGreen','DarkKhaki','DarkMagenta','DarkOliveGreen','Darkorange','DarkOrchid','DarkRed','DarkSalmon','DarkSeaGreen','DarkSlateBlue','DarkSlateGray','DarkTurquoise','DarkViolet','DeepPink','DeepSkyBlue','DodgerBlue','FireBrick','ForestGreen','Fuchsia','Gainsboro','Gold','GoldenRod','Gray','Green','GreenYellow','HotPink','IndianRed','Indigo','Ivory','Khaki','Lavender','LavenderBlush','LawnGreen','LemonChiffon','Lime','LimeGreen','Linen','Magenta','Maroon','MediumAquaMarine','MediumBlue','MediumOrchid','MediumPurple','MediumSeaGreen','MediumSlateBlue','MediumSpringGreen','MediumTurquoise','MediumVioletRed','MidnightBlue','MistyRose','Moccasin','Navy','Olive','OliveDrab','Orange','OrangeRed','Orchid','PaleGoldenRod','PaleGreen','PaleTurquoise','PaleVioletRed','PapayaWhip','PeachPuff','Peru','Pink','Plum','PowderBlue','Purple','Red','RosyBrown','RoyalBlue','SaddleBrown','Salmon','SandyBrown','SeaGreen','Sienna','Silver','SkyBlue','SlateBlue','SlateGray','Snow','SpringGreen','SteelBlue','Tan','Teal','Thistle','Tomato','Turquoise','Violet','Wheat','Yellow','YellowGreen' ]
var colors = originalColors.slice(0);

function cloneLatLng(ll) {
  return new L.LatLng(ll.lat, ll.lng);
};

var MapPage = Backbone.View.extend({
  recolorBlocks: function(blocks) {
    _.each(blocks, _.bind(function(block) {
      this.colorBlock(block, 1.0);
    }, this));
  },

  unhighlightPolygon: function() {
    console.log('unhighlighting');
    if (this.currentPaintLine_) {
      console.log('doing stuff');
      this.map_.removeLayer(this.currentPaintLine_);
      this.lastHighlightedBlocks_ = [];
      this.togglePolygonMode();
      this.currentPaintLine_ = null;
    }
  },

  doVote: function(blockids, selectedHoodId) {
    _.each(blockids, _.bind(function(blockid) {
        this.idToLayerMap_[blockid].feature.properties['votes'].push(
        {
          count: 1,
          source: 'self',
          id: selectedHoodId
        })
      }, this)
    );

  // submit the votes
    $.ajax({
      dataType: 'json',
      url: '/api/vote',
      type: 'POST',
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
  calculateBestId: function(feature) {
    return feature['properties']['id'];
  },

  calculateBestLabel: function(feature) {
    return feature['properties']['label'];
  },

  calculateColor: function(feature) {
    var bestLabel = this.calculateBestLabel(feature);
    if (!bestLabel) {
      return;
    }
    var color = this.labelColors_[bestLabel];
    if (!color) {
      if (colors.length == 0) {
        colors = originalColors;
      }
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

  recolorNeighborhoods: function() {
    console.log(this.neighborhoodIdToLayerMap_);
    _.each(this.neighborhoodIdToLayerMap_, _.bind(function(layer, id, list) {
      this.colorFeature(layer.feature, layer); 
    }, this));
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
    this.inBlockMode_ = false;
    this.idToLayerMap_ = {}
    this.idToFeatureMap_ = {}
    this.inPolygonMode_ = false;
    this.$selectedNeighborhoodSpan = $('#selectedNeighborhood');
    this.neighborhoodIdToLayerMap_ = {};

    function onEachFeature(feature, layer) {
      this.idToLayerMap_[feature.properties.id] = layer;
      this.idToFeatureMap_[feature.properties.id] = feature;
      var mouseOverCb = function(e) {
        layer.feature = feature;
        this.highlightBlock(layer, 0.75);
      }

      var mouseOutCb = function(e) {
        layer.feature = feature
        this.colorBlock(layer);
      }

      layer.feature = feature;
      layer.on('mouseover', _.bind(mouseOverCb, this));
      layer.on('mouseout', _.bind(mouseOutCb, this))
      layer.on('click', _.bind(this.processBlockClick, this, layer))
    }

    this.blockLayer_ = L.geoJson(null, {
			onEachFeature: _.bind(onEachFeature, this)
		});     

    this.blocksLoaded_ = false;

    this.labels_ = {};
    this.labelColors_ = {};
    this.apiKey_ = this.options.api_key;
    console.log(this.options);

    this.map_= L.map('map', {dragging: true}).setView([40.74, -74], 13);
   	L.tileLayer('http://{s}.tile.cloudmade.com/{key}/22677/256/{z}/{x}/{y}.png', {
			attribution: 'Map data &copy; 2011 OpenStreetMap contributors, Imagery &copy; 2012 CloudMade',
			key: 'BC9A493B41014CAABB98F0471D759707'
		}).addTo(this.map_);

    this.neighborhoodLayer_ = L.geoJson(null, {
			style: function (feature) {
				return feature.properties && feature.properties.style;
			},

			onEachFeature: _.bind(this.onEachNeighborhoodFeature, this)
		}).addTo(this.map_);
    this.neighborhoodLayer_.fire('data:loading');

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

    $('.helpButton').click(function() {
      $('#helpModal').modal();
    })
  },

  renderAreaInfo: function(data) {
    console.log('made it to areainfo')
    console.log(data)
    this.map_.fitBounds(L.geoJson(data.areas[0].bbox).getBounds());
    this.centered = true;
  },

  fetchData: function(areaid) {
    console.log('fetching ' + areaid)
    $.ajax({
      dataType: 'json',
      url: '/api/areaInfo?callback=?',
      data: {
        areaid: areaid,
        key: this.apiKey_,
      },
      success: _.bind(this.renderAreaInfo, this)
    })

    $.ajax({
      dataType: 'json',
      url: '/api/neighborhoodsByArea?callback=?',
      data: {
        areaid: areaid,
        key: this.apiKey_,
      },
      success: _.bind(this.renderData, this)
    })

   var object = {}
   this.blockLoader_ = _.extend(object, Backbone.Events);

    $.ajax({
      dataType: 'json',
      url: '/api/blocksByArea?callback=?',
      data: {
        areaid: areaid,
        key: this.apiKey_,
      },
      success: _.bind(this.cacheBlockData, this)
    })
  },

  colorFeature: function(feature, layer, opacity) {
    layer.setStyle({
      weight: 2,
      fillOpacity: opacity || 0.3,
      fillColor: this.calculateColor(feature),
      color: 'black'
    });
  },

  inPolygonMode: function() {
    return this.inPolygonMode_;
  },

  highlightBlocks: function(blockIdsResponse, opacity) {
    console.log('opacity? ' + opacity);
    opacity = opacity || 0.2;
    this.recolorBlocks(this.lastHighlightedBlocks_);

    var blocks = _.chain(blockIdsResponse['ids'])
      .map(_.bind(function(id) {
          return this.idToLayerMap_[id];
        }, this))
      .compact()
      .value();

    this.lastHighlightedBlocks_ = blocks;
    
    _.each(blocks, _.bind(function(block) {
      this.forceBlockVote(block);
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

  processPolygonDoubleClick: function(e) { 
    console.log('dblclick')
    console.log(e)
    if (this.inPolygonMode()) {
      console.log('in paint mode, trying to stop being in it')
      if (this.currentPaintLine_) {
        this.highlightBlocksByGeometry(this.currentPaintLine_.getLatLngs());
        this.unhighlightPolygon();
      }
    } 
    L.DomEvent.stopPropagation(e);
  },

  exitBlockMode: function(vote) {
    $('.controls').toggleClass('blockMode neighborhoodMode');
    this.inBlockMode_ = false;
    this.hideBlocks();
    //this.map_.removeLayer(this.blockLayer_);
    //this.map_.addLayer(this.neighborhoodLayer_);

    if (vote) {
      // go through clicked blocks
      this.colorFeature(this.lastHighlightedNeighborhood_.feature, this.lastHighlightedNeighborhood_.layer);
      var hoodId = this.lastHighlightedNeighborhood_.feature['properties']['id']
      var voteString = _.map(this.clickedBlocks_, function(feature) {
        if (feature.properties['votes'].length == 0) {
          return feature.properties['id'] + ',' + hoodId + ',-1';
        } else {
          return feature.properties['id'] + ',' + hoodId + ',1';
        }
      }).join(';')
     
      if (voteString) {
        $.ajax({
          dataType: 'json',
          url: '/api/vote',
          type: 'POST',
          data: { 
            key: this.apiKey_,
            votes: voteString
          },
          success: _.bind(this.updateHoods, this)
        });
      }
    }
    this.recolorNeighborhoods();
  },

  updateHoods: function(geojson) {
    // what we should do here is merge this with our existing geojson, sigh.
    this.neighborhoodLayer_.clearLayers();
    this.neighborhoodLayer_.addData(geojson);
  },

  reallyEnterBlockMode: function() {
    $('.controls').toggleClass('blockMode neighborhoodMode');
    // set some boolean
    this.inBlockMode_ = true;
    this.clickedBlocks_ = [];
    // swap in the block layer
    this.map_.fitBounds(this.lastHighlightedNeighborhood_.layer.getBounds());
    console.log(this.lastHighlightedNeighborhood_.feature['properties']);
    var hoodId = this.lastHighlightedNeighborhood_.feature['properties']['id']
    _.each(this.idToLayerMap_, _.bind(function(layer, id, list) {
      this.colorBlock(layer);
    }, this));
    this.blockLayer_.fire('data:loaded');
  },

  enterBlockMode: function() {
    this.hideNeighborhoods();
    //this.map_.removeLayer(this.neighborhoodLayer_);
    //this.map_.addLayer(this.blockLayer_);
    this.blockLayer_.fire('data:loading');
    if (this.blocksLoaded_) {
      this.reallyEnterBlockMode();
    } else {
      this.blockLoader_.once('loaded', _.bind(function() {
        console.log('should hide spinner');
        this.reallyEnterBlockMode();
      }, this));
    }
  },

  hideBlocks: function() {
    this.neighborhoodLayer_.bringToFront()
    this.blockLayer_.setStyle({
      'weight': 0.0,
      'fillOpacity': 0.0,
      'color': 'red'
    });
  },

  hideNeighborhoods: function() {
    this.blockLayer_.bringToFront()
    this.neighborhoodLayer_.setStyle({
      'weight': 0.0,
      'fillOpacity': 0.0,
      'color': 'orange'
    });
  },

  toggleBlockVoteHelper: function(layer, force) {
    var hoodId = this.lastHighlightedNeighborhood_.feature['properties']['id']
    var id = this.calculateBestId(layer.feature)
    this.clickedBlocks_.push(layer.feature);
    if (id != hoodId || force) {
      console.log('adding vote')
      layer.feature.properties['votes'] = [
        {
          count: 1,
          source: 'self',
          id: hoodId 
        }
      ];
    } else {
      console.log('removing vote')
      layer.feature.properties['votes'] = []
    }
  
    this.colorBlock(layer, false);

    // if it's in the hood, delete that entry
    // if it's not in the hood, add a self entry?
    // recolor it
  },
  
  toggleBlockVote: function(layer) {
    this.toggleBlockVoteHelper(layer, false)
  },
  
  forceBlockVote: function(layer) {
    this.toggleBlockVoteHelper(layer, true)
  },
  
  processBlockClick: function(layer, e) { 
    if (e.originalEvent.shiftKey) {
      if (!this.inPolygonMode_) {
        this.currentPaintLine_ = new L.Polygon([cloneLatLng(e.latlng), cloneLatLng(e.latlng)]);
        this.map_.addLayer(this.currentPaintLine_);
        this.currentPaintLine_.on('click', _.bind(this.processPolygonClick, this))
        this.currentPaintLine_.on('dblclick', _.bind(this.processPolygonDoubleClick, this))
      }

      this.lastHighlightedBlocks_ = [];

      this.togglePolygonMode();
      console.log('toggling polygon mode: we are now in polygon mode?' + this.inPolygonMode_);
    } else {
      this.toggleBlockVote(layer);
    }
  }, 

  processPolygonClick: function(e) { 
    if (e.originalEvent.shiftKey) {
      this.processPolygonDoubleClick(e);
    } else if (this.inPolygonMode()) {
      console.log('in paint mode')
      console.log(this.currentPaintLine_);
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
    }
  },
  processNeighborhoodClick: function(e) { 
    console.log('click')
    console.log(e);
    if (this.apiKey_) {
      this.enterBlockMode();
    } else {
      var modalEl = $('#loginModal')
      modalEl.modal();
    }
 
    L.DomEvent.stopPropagation(e);
  },

  togglePolygonMode: function() {
    this.inPolygonMode_ = !this.inPolygonMode_;
  },

  colorBlockHelper: function(layer, inverted, opacity) {
    var hoodId = this.lastHighlightedNeighborhood_.feature['properties']['id'];
    var id = this.calculateBestId(layer.feature);
    var color = this.calculateColor(this.lastHighlightedNeighborhood_.feature);
    if ((id == hoodId && inverted) || 
        (id != hoodId && !inverted)) {
      layer.setStyle({
        weight: 1,
        color: 'white',
        fillOpacity: 0.01
      });
    } else {
      layer.setStyle({
        weight: 1,
        color: color,
        'fillOpacity': opacity || 0.2
      });
    }
  },
  
  colorBlock: function(layer, opacity) { this.colorBlockHelper(layer, false, opacity); },
  highlightBlock: function(layer, opacity) { this.colorBlockHelper(layer, true, opacity); },

  cacheBlockData: function(geojson) { 
    console.log('loaded block layer');
    this.blocksLoaded_ = true;
    this.blockLayer_.addData(geojson)
    this.map_.addLayer(this.blockLayer_);
    this.hideBlocks();

    this.blockLoader_.trigger('loaded');
    this.map_.boxZoom.disable();
  },
   
  onEachNeighborhoodFeature: function(feature, layer) {
      layer.feature = feature;
      this.neighborhoodIdToLayerMap_[this.calculateBestId(feature)] = layer;
      console.log(this.neighborhoodIdToLayerMap_);
      if (!this.centered) {
        window.console.log(feature);
        if (feature.geometry.type == "Polygon") {
          this.map_.panTo(new L.LatLng(feature.geometry.coordinates[0][0][1], feature.geometry.coordinates[0][0][0]));
        } else {
          this.map_.panTo(new L.LatLng(feature.geometry.coordinates[0][0][0][1], feature.geometry.coordinates[0][0][0][0]));
        }
        this.centered = true;
      } 
      this.colorFeature(feature, layer); 

      layer.on('mouseover', _.bind(function(e) {
        $('.neighborhoodControls').addClass('hover');
        $('.neighborhoodControls').removeClass('nohover');
        this.colorFeature(feature, layer, 0.9);
        
        // hack, only needed by the getbounds call?
        this.lastHighlightedNeighborhood_ = {
          'layer': layer,
          'feature': feature
        }
        console.log(feature['properties']['id'] + ' mouse over');

        $('.neighborhoodInfo').html(
          this.calculateBestLabel(feature)
        );
      }, this));

      var mouseOutCb = function(e) {
        $('.neighborhoodControls').addClass('nohover');
        $('.neighborhoodControls').removeClass('hover');
        console.log(feature['properties']['id'] + ' mouse out');
        this.colorFeature(feature, layer);
      }

    layer.on('mouseout', _.bind(mouseOutCb, this))
  },

  renderData: function(geojson) {
    console.log(geojson);
    this.$polygonMode = $('#polygonMode')
    this.$polygonMode.button();
    this.$polygonMode.click(_.bind(this.togglePolygonMode, this))
    $('.exitAndSaveBlockModeButton').click(_.bind(function() { this.exitBlockMode(true); }, this)); 
    $('.exitAndUndoBlockModeButton').click(_.bind(function() { this.exitBlockMode(false); }, this)); 

    this.lastHighlightedNeighborhood_ = null;
    this.lastHighlightedBlocks_ = [];

    this.neighborhoodLayer_.addData(geojson)
    this.map_.fitBounds(this.neighborhoodLayer_.getBounds());
    this.neighborhoodLayer_.fire('data:loaded');
    
    this.neighborhoodLayer_.on('click', _.bind(this.processNeighborhoodClick, this))
 
    this.map_.on('mousemove', _.bind(function(e) {
        // console.log(e)
        if (this.inPolygonMode()) {
          console.log('moving in poly mode');
          if (this.currentPaintLine_) {
            console.log('moving in poly mode with a paint line');
            var lastIndex = this.currentPaintLine_.getLatLngs().length - 1;
            if (lastIndex == 0) {
              lastIndex = 1;
            }
            
            console.log(this.currentPaintLine_.getLatLngs())
            this.currentPaintLine_.spliceLatLngs(lastIndex, 1, cloneLatLng(e.latlng));
            console.log(this.currentPaintLine_.getLatLngs())
          }
        } 
      }, this));
  }
});
