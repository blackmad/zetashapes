L.SpinMapMixin = {
    spin: function (state) {
        var state = !!state;
        if (state) {
            // start spinning !
            console.log('spinnnn');
            console.log($('#spinner'));
            $('#spinner').show();
            if (isNaN(this._spinning)) {
              this._spinning = 0;
            }
            this._spinning++;
            console.log(this._spinning);
        }
        else {
            this._spinning--;
            console.log(this._spinning);
            if (this._spinning <= 0) {
               // end spinning !
               $('#spinner').hide();
            }
        }
    }
};

L.Map.include(L.SpinMapMixin);

L.Map.addInitHook(function () {
    this.on('layeradd', function (e) {
        // If added layer is currently loading, spin !
        if (e.layer.loading) this.spin(true);
        if (typeof e.layer.on != 'function') return;
        e.layer.on('data:loading', function () { this.spin(true) }, this);
        e.layer.on('data:loaded',  function () { this.spin(false) }, this);
    }, this);
    this.on('layerremove', function (e) {
        // Clean-up
        if (e.layer.loading) this.spin(false);
        if (typeof e.layer.on != 'function') return;
        e.layer.off('data:loaded');
        e.layer.off('data:loading');
    }, this);
});

