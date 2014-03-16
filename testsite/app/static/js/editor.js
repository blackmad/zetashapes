// TODO
// figure out why clicking blocks isn't working
// make label colors repro

var originalColors = [ 'Aqua','Aquamarine','Blue','BlueViolet','Brown','BurlyWood','CadetBlue','Chartreuse','Chocolate','Coral','CornflowerBlue','Crimson','Cyan','DarkBlue','DarkCyan','DarkGoldenRod','DarkGray','DarkGreen','DarkKhaki','DarkMagenta','DarkOliveGreen','Darkorange','DarkOrchid','DarkRed','DarkSalmon','DarkSeaGreen','DarkSlateBlue','DarkSlateGray','DarkTurquoise','DarkViolet','DeepPink','DeepSkyBlue','DodgerBlue','FireBrick','ForestGreen','Fuchsia','Gold','GoldenRod','Gray','Green','GreenYellow','HotPink','IndianRed','Indigo','LawnGreen','Lime','LimeGreen','Magenta','Maroon','MediumAquaMarine','MediumBlue','MediumOrchid','MediumPurple','MediumSeaGreen','MediumSlateBlue','MediumSpringGreen','MediumTurquoise','MediumVioletRed','MidnightBlue','Navy','Olive','OliveDrab','Orange','OrangeRed','Orchid','PaleGreen','PaleTurquoise','PaleVioletRed','Peru','Pink','Plum','Purple','Red','RosyBrown','RoyalBlue','SaddleBrown','Salmon','SandyBrown','SeaGreen','Sienna','SkyBlue','SlateBlue','SlateGray','SpringGreen','SteelBlue','Tan','Teal','Thistle','Tomato','Turquoise','Violet','Wheat','Yellow','YellowGreen' ]
var colors = originalColors.slice(0);

function cloneLatLng(ll) {
  return new L.LatLng(ll.lat, ll.lng);
};

$.parseParams = function(p){
var ret = {},
    seg = p.replace(/^\?/,'').split('&'),
    len = seg.length, i = 0, s;
for (;i<len;i++) {
    if (!seg[i]) { continue; }
    s = seg[i].split('=');
    ret[s[0]] = s[1];
}
return ret;}

var MapPage = Backbone.View.extend({
  debugLog: function(s) {
    if (this.debug_) {
      console.log(s);
    }
  },

  recolorBlocks: function(blocks) {
    _.each(blocks, _.bind(function(block) {
      this.colorBlock(block, 1.0);
    }, this));
  },

  unhighlightPolygon: function() {
    this.debugLog('unhighlighting');
    if (this.currentPaintLine_) {
      this.debugLog('doing stuff');
      this.map_.removeLayer(this.currentPaintLine_);
      this.lastHighlightedBlocks_ = [];
      this.togglePolygonMode();
      this.currentPaintLine_ = null;
    }
  },

  getCurrentBlockIds: function() {
    var blockids = _.map(this.lastHighlightedBlocks_, function(f) {
      return f.feature['properties']['id'];
    });
    return blockids;
  },

  calculateColor: function(feature) {
    var bestLabel = feature.properties.id;
    if (!bestLabel) {
      return;
    }
    var color = this.labelColors_[bestLabel];
    if (!color) {
      if (colors.length == 0) {
        colors = originalColors;
      }
      //var randomnumber=Math.floor(Math.random()*colors.length)
      color = colors[0];
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

  setCurrentNeighborhoodName: function(name) {
    // $('.neighborhoodInfo').html(name);
  },

  recolorNeighborhoods: function() {
    this.debugLog(this.neighborhoodIdToLayerMap_);
    _.each(this.neighborhoodIdToLayerMap_, _.bind(function(layer, id, list) {
      this.colorNeighborhoodFeature(layer.feature, layer); 
    }, this));
  },

  toggleDrawMode: function(one, two) {
    if (this.drawMode_ == one) {
      this.drawMode_ = two;
      $('.drawMode').html(two);
    } else {
      this.drawMode_ = one;
      $('.drawMode').html(one);
    }
  },

  changePolygonMode: function(m) {
    this.polygonModeAction_ = m;
    $('.polygonModeAction').html(m);

    if (m == 'redraw') {
      _.each(this.lastHighlightedNeighborhood_.feature.properties.blockids, _.bind(function(id) {
        var layer = this.idToLayerMap_[id];
        this.forceBlockLayerUnVote(layer);
      }, this));

    }
  },

  onEachBlockFeature: function(feature, layer) {
    this.idToLayerMap_[feature.properties.id] = layer;
    this.idToFeatureMap_[feature.properties.id] = feature;
    var mouseOverCb = function(e) {
      if (!this.inBlockMode_) {
        return;
      }

      this.debugLog(feature.properties.id);
      layer.feature = feature;
      if (this.drawMode_ == 'continuous') {
        this.doVoteOnBlockLayer(layer);
      }
      this.highlightBlock(layer, 0.75);
    }

    var mouseOutCb = function(e) {
      if (!this.inBlockMode_) {
        return;
      }
      layer.feature = feature
      this.colorBlock(layer);
    }

    layer.feature = feature;
    layer.on('mouseover', _.bind(mouseOverCb, this));
    layer.on('mouseout', _.bind(mouseOutCb, this))
    layer.on('click', _.bind(this.processBlockClick, this, layer))
  },

  initialize: function() {
    this.debug_ = false;
    this.params_ = $.parseParams((window.location.search || window.location.hash).substring(1));
    if (this.params_['debug']) {
      this.debug_ = true;
    }

    key('c', _.bind(function(){ this.toggleDrawMode('continuous', 'polygon') }, this));
    key('p', _.bind(function(){ this.toggleDrawMode('polygon', 'continous') }, this));
    key('r', _.bind(function(){ this.changePolygonMode('redraw') }, this));
    key('d', _.bind(function(){ this.changePolygonMode('delete') }, this));
    key('a', _.bind(function(){ this.changePolygonMode('add') }, this));

    this.requestsOutstanding_ = 0;
    this.neighborhoodsLoaded_ = false;
    this.inBlockMode_ = false;
    this.idToLayerMap_ = {}
    this.idToFeatureMap_ = {}
    this.inPolygonMode_ = false;
    this.$selectedNeighborhoodSpan = $('#selectedNeighborhood');
    this.neighborhoodIdToLayerMap_ = {};
    this.addHoodTempId_ = -1;
 
    this.blockLayer_ = L.geoJson(null, {
			onEachFeature: _.bind(this.onEachBlockFeature, this)
		});     

    this.blocksLoaded_ = false;

    this.labelColors_ = {};
    this.apiKey_ = this.options.api_key;
    this.debugLog(this.options);

    this.map_= L.map('map', {dragging: true}).setView([40.74, -74], 13);
    var mapboxTilesAttr = 'Tiles &copy; <a href="http://www.mapbox.com/about/maps/">Mapbox</a>, Data &copy; OSM';

   	L.tileLayer(
        'http://{s}.tiles.mapbox.com/v3/foursquare.map-t2z7w2jz/{z}/{x}/{y}.png',
        {
          subdomains: 'abcd',
          attribution: mapboxTilesAttr 
        }
    ).addTo(this.map_);

    this.neighborhoodLayer_ = L.geoJson(null, {
			style: function (feature) {
				return feature.properties && feature.properties.style;
			},

			onEachFeature: _.bind(this.onEachNeighborhoodFeature, this)
		}).addTo(this.map_);
    this.neighborhoodLayer_.fire('data:loading');

    if (this.options.geojson) {
      this.renderData(this.options.geojson);
    } else {
      this.fetchData(this.options.areaid);
      this.fetchNearbyData(this.options.areaid);
    }

    $('.helpButton').click(function() {
      $('#helpModal').modal();
    })
  },

  renderAreaInfo: function(data) {
    this.debugLog('made it to areainfo')
    this.debugLog(data)
    this.map_.fitBounds(L.geoJson(data.areas[0].bbox).getBounds());
    this.updateStatus('Loading blocks ...')
    this.neighborhoodLabels_ = data.areas[0].neighborhoods;
    this.cityLabels_ = data.areas[0].cities;
    this.centered = true;
  },

  renderNearbyAreaInfo: function(data) {
    this.debugLog('made it to areainfo')
    this.debugLog(data)
    _.each(data.areas, function(area) {
        var geom = L.geoJson(area.geom);
        geom.bindLabel('Click to load ' + area.displayName);
        this.map_.addLayer(geom);

        var mouseOverCb = function(e) {
          geom.setStyle(this.grayStyleHover);
        }
        var mouseOutCb = function(e) {
          geom.setStyle(this.grayStyle);
        }
        geom.setStyle(this.grayStyle);

        geom.on('mouseover', _.bind(mouseOverCb, this));
        geom.on('mouseout', _.bind(mouseOutCb, this))

    }, this);
  },

  fetchNearbyData: function(areaid) {
   this.debugLog('fetching ' + areaid)
    $.ajax({
      dataType: 'json',
      url: '/api/nearbyAreas?callback=?',
      data: {
        'areaid': areaid
      },
      success: _.bind(this.renderNearbyAreaInfo, this)
    })
  },

  fetchData: function(areaid) {
    this.debugLog('fetching ' + areaid)
    $.ajax({
      dataType: 'json',
      // url: '/static/json/info-' + areaid + '.json',
      url: '/api/areaInfo?callback=?',
      data: {
        'areaid': areaid
      },
      success: _.bind(this.renderAreaInfo, this)
    }); 

    this.requestsOutstanding_ += 1
    $.ajax({
      dataType: 'json',
      url: '/api/neighborhoodsByArea?callback=?',
      data: {
        areaid: areaid,
        key: this.apiKey_,
      },
      success: _.bind(this.renderData, this)
    })

   if (this.apiKey_) {
     this.requestsOutstanding_ += 1;
     var object = {}
     this.blockLoader_ = _.extend(object, Backbone.Events);
      $.ajax({
        dataType: 'json',
        url: '/static/json/' + areaid + '.json',
        data: {
          areaid: areaid,
          key: this.apiKey_,
        },
        success: _.bind(this.cacheBlockData, this)
      })
   } else {
    this.neighborhoodLayer_.on('click', _.bind(this.processNeighborhoodClick, this));
   }
  },

  colorNeighborhoodFeature: function(feature, layer, opacity) {
    if (!layer) {
      return;
    }
    if (this.inBlockMode_) {
      layer.setStyle(this.clearStyle);
    } else {
      layer.setStyle({
        weight: 2,
        fillOpacity: opacity || 0.3,
        fillColor: this.calculateColor(feature),
        color: 'black'
      });
    }
  },

  inPolygonMode: function() {
    return this.inPolygonMode_;
  },

  doVoteOnBlockLayer: function(block){ 
    if (this.polygonModeAction_ == 'delete') {
      this.forceBlockLayerUnVote(block);
    } else {
      this.forceBlockLayerVote(block);
    }
  },

  highlightBlocks: function(blockIdsResponse, opacity) {
    this.debugLog('opacity? ' + opacity);
    opacity = opacity || 0.2;
    this.recolorBlocks(this.lastHighlightedBlocks_);

    var blocks = _.chain(blockIdsResponse['ids'])
      .map(_.bind(function(id) {
          return this.idToLayerMap_[id];
        }, this))
      .compact()
      .value();

    this.lastHighlightedBlocks_ = blocks;
    
    _.each(blocks, _.bind(this.doVoteOnBlockLayer, this));
  },

  highlightBlocksByGeometry: function(latlngs) {
    var lls = _.map(latlngs.concat([latlngs[0]]), function(ll) { return ll.lng + ' ' + ll.lat }).join(',')
    this.debugLog('firing off highlight blocks')
    $.ajax({
      dataType: 'json',
      url: '/api/blocksByGeom?callback=?',
      data: { ll: lls },
      success: _.bind(this.highlightBlocks, this)
    })

  },

  processPolygonDoubleClick: function(e) { 
    this.debugLog('dblclick')
    this.debugLog(e)
    if (this.inPolygonMode()) {
      this.debugLog('in paint mode, trying to stop being in it')
      if (this.currentPaintLine_) {
        this.highlightBlocksByGeometry(this.currentPaintLine_.getLatLngs());
        this.unhighlightPolygon();
      }
    }
  },

  doVote: function(voteString) {
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
  },

  doAdd: function() {
    var blockIds = _.map(this.clickedBlocks_, function(b){ return b.properties.id });
    var cityId = this.lastHighlightedNeighborhood_.feature['properties']['city'];
    var hoodLabel =  this.lastHighlightedNeighborhood_.feature['properties']['label'];
    
    if (blockIds) {
      $.ajax({
          dataType: 'json',
          url: '/api/addHood',
          type: 'POST',
          data: { 
            key: this.apiKey_,
            label: hoodLabel,
            parentid: cityId,
            blockids: blockIds.join(',')
          },
          success: _.bind(this.updateHoods, this)
        });
    }
  },

  exitBlockMode: function(vote) {
    $('.controls').toggleClass('blockMode neighborhoodMode');
    this.inBlockMode_ = false;
    this.hideBlocks();
    //this.map_.removeLayer(this.blockLayer_);
    //this.map_.addLayer(this.neighborhoodLayer_);

    if (vote) {
      this.colorNeighborhoodFeature(
        this.lastHighlightedNeighborhood_.feature, 
        this.lastHighlightedNeighborhood_.layer
      );
      var hoodId = this.lastHighlightedNeighborhood_.feature['properties']['id']
      if (this.lastHighlightedNeighborhood_.feature['properties']['needsAdd']) {
        this.doAdd();
      } else {
        var voteString = _.map(this.clickedBlocks_, function(feature) {
          if (!feature.properties.hoodId) {
            return feature.properties.id + ',' + hoodId + ',-1';
          } else {
            return feature.properties.id + ',' + hoodId + ',1';
          }
        }).join(';')
       
        this.doVote(voteString); 
      }
    } else {
      _.each(this.clickedBlocks_, function(feature) {
        feature.properties.hoodId = feature.properties.originalHoodId;
      })
    }
    this.recolorNeighborhoods();
  },

  updateHoods: function(geojson) {
    // what we should do here is merge this with our existing geojson, sigh.
    this.neighborhoodLayer_.clearLayers();
    this.neighborhoodLayer_.addData(geojson);
    this.neighborhoodGeoJson_ = geojson;
    this.labelBlocks();
  },

  reallyEnterBlockMode: function() {
    this.changePolygonMode('add');
    this.toggleDrawMode('polygon', 'polygon');
    $('.controls').toggleClass('blockMode neighborhoodMode');
    // set some boolean
    this.inBlockMode_ = true;
    this.clickedBlocks_ = [];
    // swap in the block layer
    if (this.lastHighlightedNeighborhood_.layer) {
      this.map_.fitBounds(this.lastHighlightedNeighborhood_.layer.getBounds());
    }
    this.debugLog(this.lastHighlightedNeighborhood_.feature['properties']);
    var hoodId = this.lastHighlightedNeighborhood_.feature['properties']['id']
    this.blockLayer_.setStyle(this.lightStyle);

    _.each(this.lastHighlightedNeighborhood_.feature.properties.blockids, _.bind(function(id) {
      var layer = this.idToLayerMap_[id];
      this.colorBlock(layer);
    }, this));
    if (this.lastHighlightedNeighborhood_.layer) {
      this.lastHighlightedNeighborhood_.layer.setStyle(this.clearStyle);
    }
  },

  enterBlockMode: function() {
    if (!window.localStorage.getItem("zetashapes.showedHelp")) { 
      window.localStorage.setItem("zetashapes.showedHelp", '1')
      $('#helpModal').modal();
    }

    this.hideNeighborhoods();
    //this.map_.removeLayer(this.neighborhoodLayer_);
    //this.map_.addLayer(this.blockLayer_);
    if (this.blocksLoaded_) {
      this.reallyEnterBlockMode();
    } else {
      this.blockLoader_.once('loaded', _.bind(function() {
        this.debugLog('should hide spinner');
        this.reallyEnterBlockMode();
      }, this));
    }
  },

  clearStyle: {
    'weight': 0.0,
    'fillOpacity': 0.0,
    'color': 'red'
  },

  lightStyle: {
    weight: 1,
    color: 'white',
    fillColor: 'white',
    fillOpacity: 0.01
  },

  grayStyle : {
    'weight': 0.5,
    'fillOpacity': 0.0,
    'color': 'gray'
  },
   grayStyleHover : {
    'weight': 0.5,
    'fillOpacity': 0.4,
    'color': 'gray'
  },

  highlightBlockStyle: function(color) { return {
    weight: 3,
    color: 'black',
    fillColor: color,
    fillOpacity: 0.5
  }},

  hideBlocks: function() {
    this.neighborhoodLayer_.bringToFront()
    this.blockLayer_.setStyle(this.clearStyle);
  },

  hideNeighborhoods: function() {
    this.blockLayer_.bringToFront()
    this.neighborhoodLayer_.setStyle(this.clearStyle);
  },

  toggleBlockVoteHelper: function(layer, force, mode) {
    var hoodId = this.lastHighlightedNeighborhood_.feature['properties']['id']
    var id = layer.feature.properties.hoodId;
    this.clickedBlocks_.push(layer.feature);
    if (!layer.feature.properties.originalHoodId) {
      layer.feature.properties.originalHoodId = layer.feature.properties.hoodId;
    }

    if ((!force && id != hoodId) || (force && mode != 'delete')) {
      this.debugLog('adding vote')
      layer.feature.properties.hoodId = hoodId;
    } else {
      this.debugLog('removing vote')
      layer.feature.properties.hoodId = null;
    }
  
    this.colorBlock(layer, false);

    // if it's in the hood, delete that entry
    // if it's not in the hood, add a self entry?
    // recolor it
  },
  
  toggleBlockVote: function(layer) {
    this.toggleBlockVoteHelper(layer, false)
  },
  
  forceBlockLayerVote: function(layer) {
    this.toggleBlockVoteHelper(layer, true)
  },

  forceBlockLayerUnVote: function(layer) {
    var mode = '';
    this.toggleBlockVoteHelper(layer, true, 'delete');
  },
  
  processBlockClick: function(layer, e) { 
    if (!this.inBlockMode_) {
      return;
    }

    if (e.originalEvent.altKey || e.originalEvent.metaKey) {
      if (!this.inPolygonMode_) {
        this.currentPaintLine_ = new L.Polygon([cloneLatLng(e.latlng), cloneLatLng(e.latlng)]);
        this.map_.addLayer(this.currentPaintLine_);
        this.currentPaintLine_.on('click', _.bind(this.processPolygonClick, this))
        this.currentPaintLine_.on('dblclick', _.bind(this.processPolygonDoubleClick, this))
      }

      this.lastHighlightedBlocks_ = [];

      this.togglePolygonMode();
      this.debugLog('toggling polygon mode: we are now in polygon mode?' + this.inPolygonMode_);
    } else {
      if (this.drawMode_ != 'continuous') {
        this.toggleBlockVote(layer);
      }
    }
  }, 

  processPolygonClick: function(e) { 
    if (e.originalEvent.altKey || e.originalEvent.metaKey) {
      this.processPolygonDoubleClick(e);
    } else if (this.inPolygonMode()) {
      this.debugLog('in paint mode')
      this.debugLog(this.currentPaintLine_);
      if (this.currentPaintLine_) {
        var lastIndex = this.currentPaintLine_.getLatLngs().length - 1
        this.debugLog(this.currentPaintLine_.getLatLngs()[0].distanceTo(e.latlng));
        this.highlightBlocksByGeometry(this.currentPaintLine_.getLatLngs())
        if (this.currentPaintLine_.getLatLngs()[0].distanceTo(e.latlng) < 100) {
          this.currentPaintLine_ = null;
        } else {
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
    this.debugLog('click')
    this.debugLog(e);
    if (this.apiKey_) {
      this.enterBlockMode();
    } else {
      if (this.loginAlert_) {
        $('body').append(mapPage.loginAlert_)
      } else {
        this.loginAlert_ = $('.loginAlert').clone()
        $('body').append(this.loginAlert_)
        this.loginAlert_.show();
      }
    }
 
    L.DomEvent.stopPropagation(e);
  },
  
  processNeighborhoodDoubleClick: function(e) { 
    this.map_.setZoom(this.map_.getZoom() + 1);
  },

  togglePolygonMode: function() {
    this.inPolygonMode_ = !this.inPolygonMode_;
  },

  updateStatus: function(str) {
    $('#spinner').html(str);
  },

  colorBlockHelper: function(layer, inverted, opacity, setCursor) {
    if (! this.lastHighlightedNeighborhood_) {
      return;
    }
    var hoodId = this.lastHighlightedNeighborhood_.feature['properties']['id'];
    var id = layer.feature.properties.hoodId;
    var color = this.calculateColor(this.lastHighlightedNeighborhood_.feature);
    if ((id == hoodId && inverted) || 
        (id != hoodId && !inverted)) {
      style = this.lightStyle;
      if (opacity) {
        style = this.highlightBlockStyle('white');
      }
      layer.setStyle(style);
    } else {
      style = {
        weight: 1,
        color: 'black',
        fillColor: color,
        'fillOpacity': opacity || 0.2
      };
      if (opacity) {
        style = this.highlightBlockStyle(color);
      }
      layer.setStyle(style);
    }
  },
  
  colorBlock: function(layer, opacity) { this.colorBlockHelper(layer, false, opacity); },
  highlightBlock: function(layer, opacity) { this.colorBlockHelper(layer, this.drawMode_ != 'continuous', opacity, true); },

  cacheBlockData: function(geojson) { 
    this.updateStatus('loaded census blocks')

    this.debugLog('loaded block layer');
    this.blocksLoaded_ = true;
    this.blockLayer_.addData(geojson)
    this.updateStatus('built block layer');
    this.map_.addLayer(this.blockLayer_);
    this.updateStatus('added block layer to map');
    this.hideBlocks();
    this.updateStatus('hiding block layer until later');
    this.updateStatus('Reticulating Splines ...');

    this.blockLoader_.trigger('loaded');
    // this.map_.boxZoom.disable();
    if (this.neighborhoodsLoaded_) {
      this.labelBlocks();
    }
    this.neighborhoodLayer_.on('click', _.bind(this.processNeighborhoodClick, this));
    this.neighborhoodLayer_.on('dblclick', _.bind(this.processNeighborhoodDoubleClick, this));
    this.requestDone();
  },
   
  onEachNeighborhoodFeature: function(feature, layer) {
      layer.feature = feature;
      this.neighborhoodIdToLayerMap_[feature.properties.id] = layer;
      if (!this.centered) {
        this.debugLog(feature);
        if (feature.geometry.type == "Polygon") {
          this.map_.panTo(new L.LatLng(feature.geometry.coordinates[0][0][1], feature.geometry.coordinates[0][0][0]));
        } else {
          this.map_.panTo(new L.LatLng(feature.geometry.coordinates[0][0][0][1], feature.geometry.coordinates[0][0][0][0]));
        }
        this.centered = true;
      } 
      this.colorNeighborhoodFeature(feature, layer); 
      
      layer.bindLabel(feature.properties.label);

      layer.on('mouseover', _.bind(function(e) {
        $('.neighborhoodControls').addClass('hover');
        $('.neighborhoodControls').removeClass('nohover');
        this.colorNeighborhoodFeature(feature, layer, 0.9);
        
        // hack, only needed by the getbounds call?
        this.lastHighlightedNeighborhood_ = {
          'layer': layer,
          'feature': feature
        }
        this.debugLog(feature['properties']['id'] + ' mouse over ' + this.calculateColor(feature));

        this.setCurrentNeighborhoodName(feature.properties.label);
      }, this));

      var mouseOutCb = function(e) {
        $('.neighborhoodControls').addClass('nohover');
        $('.neighborhoodControls').removeClass('hover');
        this.debugLog(feature['properties']['id'] + ' mouse out');
        this.colorNeighborhoodFeature(feature, layer);
      }

    layer.on('mouseout', _.bind(mouseOutCb, this))
  },

  labelBlocks: function() {
    this.updateStatus('matching neighborhood labels to blocks');
    this.debugLog('labeling blocks');
    _.each(this.neighborhoodGeoJson_.features, _.bind(function(f) {
      var me = this;
      _.each(f.properties.blockids, function(bid) {
        var block = me.idToFeatureMap_[bid];
        if (block) {
          block.properties['hoodId'] = f.properties.id;
        } else {
          this.debugLog('no block for ' + bid);
        }
      })
    }, this));
  },

  requestDone: function() {
    this.requestsOutstanding_--;
    this.debugLog(this.requestsOutstanding_)
    if (this.requestsOutstanding_ == 0) {
      this.neighborhoodLayer_.fire('data:loaded');
      $('.controls').toggleClass('loading loaded');
    }
  },

  setupDeleteNeighborhoodModal: function() {
    var modal = $('#neighborhoodDeleteModal');
    var select = modal.find('.neighborhoodSelect');
    _.each(_.sortBy(this.neighborhoodLabels_, function(l) { return l['label']; }), function(label) {
      select.append($('<option>', { value: label['id'] }).text(label['label']));
    });
    
    modal.find('.reassignButton').click(_.bind(function() {
      var voteString = 
        _.map(this.lastHighlightedNeighborhood_.feature.properties.blockids, function(blockid) {
          var votes = [blockid, this.lastHighlightedNeighborhood_.feature.properties.id, '-1'].join(',') + ';' +
            [blockid, select.val(), '1'].join(',');
          return votes;
        }, this).join(';');
     
      this.doVote(voteString); 

      modal.modal('hide');
      this.exitBlockMode(false);
    }, this));

    modal.find('.deleteHoodButton').click(_.bind(function() {
      var voteString = 
        _.map(this.lastHighlightedNeighborhood_.feature.properties.blockids, function(blockid) {
          return [blockid, this.lastHighlightedNeighborhood_.feature.properties.id, '-1'].join(',');
        }, this).join(';')
     
      this.doVote(voteString); 

      modal.modal('hide');
      this.exitBlockMode(false);
    }, this));
 
    modal.find('.closeButton').click(function() {
      modal.modal('hide');
    });
  },

  setupAddNeighborhoodModal: function() {
    var modal = $('#neighborhoodAddModal');
    
    modal.find('.closeButton').click(function() {
      modal.modal('hide');
    });

    modal.find('.addButton').click(_.bind(function() {
      var neighborhoodMap = _.indexBy(this.neighborhoodLabels_, 'label')
      var sel = modal.find('.hoodEntry');
      var selectedHood = sel.val();
      var hoodId = null
      if (neighborhoodMap[selectedHood]) {
        neighborhoodMap[selectedHood]['id'];
      }
      var layer = this.neighborhoodIdToLayerMap_[hoodId];

      if (!hoodId || !layer) {
        if (hoodId == undefined) {
          hoodId = this.addHoodTempId_;
        }

        this.lastHighlightedNeighborhood_ = {
          'feature': {
            'properties': {
              'label': selectedHood,
              'id': hoodId,
              'needsAdd': true,
              'city': modal.find('.citySelect').val(),
              'blockids': []
            }
          }
        };
        this.addHoodTempId_ -= 1;
      } else {
        this.lastHighlightedNeighborhood_ = {
          'layer': layer,
          'feature': layer.feature 
        };
      }
      modal.modal('hide');
      $('.controls').show();
      this.setCurrentNeighborhoodName(selectedHood);
      this.enterBlockMode();
    }, this));

    modal.on('hidden.bs.modal', function (e) {
      $('.controls').show();
    });
  },

  deleteNeighborhood: function() {
    console.log('entering deleteNeighborhod')
    console.log(this)
    var modal = $('#neighborhoodDeleteModal');

    modal.find('.neighborhoodName').html(
      this.lastHighlightedNeighborhood_.feature.properties.label
    );
   
    modal.modal()
  },

  addNeighborhood: function() {
    console.log('entering addNeighborhod')
    console.log(this)
    $('.controls').hide();
    var modal = $('#neighborhoodAddModal');

    var hoodSelect = modal.find('.neighborhoodSelect');
    _.each(_.sortBy(this.neighborhoodLabels_, function(l) { return l['label']; }), function(label) {
      hoodSelect.append($('<option>', { value: label['id'] }).text(label['label']));
    });

    var sel = modal.find('.hoodEntry');
    var neighborhoodMap = _.indexBy(this.neighborhoodLabels_, 'label')
    var source = _.map(neighborhoodMap, function(c) { return c['label']; })
    sel.typeahead({
      source: source,
      updater: function(selection){
        console.log("You selected: " + selection)
        return selection;
      }
    });

    var citySelect = modal.find('.citySelect');
    _.each(_.sortBy(this.cityLabels_, function(l) { return l['label']; }), function(label) {
      citySelect.append($('<option>', { value: label['id'] }).text(label['label']));
    });

    modal.modal()
  },

  renderData: function(geojson) {
    this.updateStatus('loaded neighborhood outlines');
    this.neighborhoodsLoaded_ = true;
    this.$polygonMode = $('#polygonMode')
    this.$polygonMode.button();
    this.$polygonMode.click(_.bind(this.togglePolygonMode, this))
    $('.exitAndSaveBlockModeButton').click(_.bind(function() { this.exitBlockMode(true); }, this)); 
    $('.exitAndUndoBlockModeButton').click(_.bind(function() { this.exitBlockMode(false); }, this)); 
    console.log('renderData');
    $('.deleteButton').click(_.bind(function() { this.deleteNeighborhood(); }, this)); 
    this.setupDeleteNeighborhoodModal();

    $('.addButton').click(_.bind(function() { this.addNeighborhood(); }, this)); 
    this.setupAddNeighborhoodModal();

    this.lastHighlightedNeighborhood_ = null;
    this.lastHighlightedBlocks_ = [];
    this.neighborhoodGeoJson_ = geojson;

    this.updateStatus('loading neighborhoods to layer')
    this.neighborhoodLayer_.addData(geojson)
    this.updateStatus('neighborhood layer done processing');
    this.map_.fitBounds(this.neighborhoodLayer_.getBounds());
     
    this.map_.on('mousemove', _.bind(function(e) {
        // this.debugLog(e)
        if (this.inPolygonMode()) {
          this.debugLog('moving in poly mode');
          if (this.currentPaintLine_) {
            this.debugLog('moving in poly mode with a paint line');
            var lastIndex = this.currentPaintLine_.getLatLngs().length - 1;
            if (lastIndex == 0) {
              lastIndex = 1;
            }
            
            this.debugLog(this.currentPaintLine_.getLatLngs())
            this.currentPaintLine_.spliceLatLngs(lastIndex, 1, cloneLatLng(e.latlng));
            this.debugLog(this.currentPaintLine_.getLatLngs())
          }
        } 
      }, this));

    if (this.blocksLoaded_) {
      this.labelBlocks();
    }
    this.requestDone();
  }
});
