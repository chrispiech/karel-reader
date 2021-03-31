

// that.beepers class
function Beepers(rows, cols) {

   var that = {};

	that.beepers = new Array();
	for (var i = 0; i < rows; i++) {
		that.beepers[i] = new Array();
		for (var j = 0; j < cols; j++) {
			that.beepers[i][j] = 0;
		}
	}

	that.equals = function(other) {
      for (var i = 0; i < rows; i++) {
		   for (var j = 0; j < cols; j++) {
			   if(that.beepers[i][j] != other.beepers[i][j]) {
			      return false;
		      }
		   }
	   }
      return true;
	}

	that.beeperPresent = function(r, c) {
		return that.beepers[r][c] > 0;
	}

	that.putBeeper = function(r, c) {
		that.beepers[r][c] = that.beepers[r][c] + 1;
	}

	that.pickBeeper = function(r, c) {
		that.beepers[r][c] = that.beepers[r][c] - 1;
	}

	that.getNumBeepers = function(r, c) {
      return that.beepers[r][c];
	}

  that.totalBeepers = function() {
    // returns total number of beepers in world
    const reducer = (accumulator, currentValue) => accumulator + currentValue;
    return that.beepers.flat().reduce(reducer);
  }

  that.beeperText = function(){
    var beepersLeft = that.totalBeepers();
    if (beepersLeft == 0){
      console.log('No beepers are present.');
      return;
      // return 'No beepers are present.';
    }

    var toPrint = 'The beepers are placed as follows:';
    for (var i = 0; i < rows; i++) {
      for (var j = 0; j < cols; j++) {
        var numBeepers = that.beepers[i][j];
        if(numBeepers > 0) {
          toPrint = toPrint.concat(`\n${numBeepers} beeper at row ${i}, column ${j}`);
          beepersLeft = beepersLeft - numBeepers;
         }
         if(beepersLeft == 0){
           // all beepers have been accounted for
           console.log(toPrint);
           return;
           // return toPrint;
         }
      }
    }
  }

	that.deepCopy = function() {
      var newModel = Beepers(rows, cols);
      newModel.beepers = deepCopyUtil(that.beepers);
      return newModel;
	}

	return that;
}
