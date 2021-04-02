/**
 * Class: Karel
 * ------------
 * The Karel class is the controller (as in MVC) of Karel and
 * Karel's world. Karel is implemented using an underlying
 * KarelModel which is rendered using a static KarelView
 * draw method.
 */
function Karel(canvasModel, codeLanguage, language) {

  let PATH_TO_ROOT = '../../'

  // uses a flag to know if it is loaded
  var that = {
    'isLoaded':false
  };

  var karelModel = KarelModel();

  that.addMoveText = console.log; // will be overwritten with function that modifies DOM to add move text

  that.draw = function(c) {
     KarelView.draw(canvasModel, karelModel, c);
  }

  that.move = function() {
    karelModel.move();
    that.addMoveText(karelModel.moveText('moved one step forward'));
  }

  that.turnLeft = function() {
    karelModel.turnLeft();
    that.addMoveText(karelModel.moveText('turned left'));
  }

  that.turnRight = function() {
    karelModel.turnRight();
    that.addMoveText(karelModel.moveText('turned right'));
  }

  that.turnAround = function() {
    karelModel.turnAround();
    that.addMoveText(karelModel.moveText('turned around'));
  }

  that.paintCorner = function(color) {
    karelModel.paintCorner(color);
    that.addMoveText(karelModel.moveText(`painted the corner ${color}`));
  }

  that.putBeeper = function() {
    karelModel.putBeeper();
    that.addMoveText(karelModel.moveText('put a beeper down'));
  }

  that.pickBeeper = function() {
    karelModel.pickBeeper();
    that.addMoveText(karelModel.moveText('picked a beeper up'));
  }

   that.beepersInBag = function () {
      return karelModel.getNBeepersInBag() > 0
   }

   that.noBeepersInBag = function() {
     return karelModel.getNBeepersInBag() <= 0
   }

  that.beepersPresent = function() {
    return karelModel.beeperPresent();
  }

  that.noBeepersPresent = function() {
    return !karelModel.beeperPresent();
  }

   that.frontIsClear = function() {
      return karelModel.frontIsClear();
  }

  that.frontIsBlocked = function() {
      return !karelModel.frontIsClear();
  }

  that.random = function(p) {
      var prob = 0.5;
      if (p != undefined) {
         prob = p;
      }
      return Math.random() > prob;
  }

  that.rightIsClear = function() {
    return karelModel.rightIsClear();
  }

  that.rightIsBlocked = function() {
    return !karelModel.rightIsClear();
  }

  that.leftIsClear = function() {
    return karelModel.leftIsClear();
  }

   that.leftIsBlocked = function() {
    return !karelModel.leftIsClear();
  }

  that.facingNorth = function() {
    return karelModel.facingNorth();
  }

  that.notFacingNorth = function() {
    return !karelModel.facingNorth();
  }

  that.facingSouth = function() {
    return karelModel.facingSouth();
  }

  that.notFacingSouth = function() {
    return !karelModel.facingSouth();
  }

  that.facingEast = function() {
    return karelModel.facingEast();
  }

  that.notFacingEast = function() {
    return !karelModel.facingEast();
  }

  that.facingWest = function() {
    return karelModel.facingWest();
  }

  that.notFacingWest = function() {
    return !karelModel.facingWest();
  }

  that.loadWorld = function(text, canvasModel) {
    karelModel.loadWorld(text, canvasModel);
  }

  that.getModel = function() {
    return karelModel;
  }

  that.getInitialWorldText = function(customDescription) {
    return karelModel.initialWorldText(customDescription);
  }

  that.getMoveText = function(action) {
    return karelModel.moveText(action);
  }

  // load language API
  let path = PATH_TO_ROOT + "/karel/js/api/" + codeLanguage + '/' + language + ".json"
  loadDoc(path, function(jsonTxt) {
    var json = JSON.parse(jsonTxt)
    initLanguageAPI(json)
  })

  function initLanguageAPI(transDict) {
    console.log(transDict)
    // add translation to instructions set
    for(original in transDict) {
      translation = transDict[original]
      if(original in Karel.instructions){
        v = Karel.instructions[original]
        Karel.instructions[translation] = v
      }
      if(original in Karel.predicates) {
        v = Karel.predicates[original]
        Karel.predicates[translation] = v
      }
    }
    console.log('that')
    console.log(that)

    // add translation methods
    for(original in transDict) {

      console.log(that['move'])
      translation = transDict[original]
      that[translation] = that[original];
    }
    that.isLoaded = true;
  }

  // don't return the class until the language model has been loaded
  while(!that.isLoaded) {
    console.log('not loaded...')
  }

  console.log(that)

  return that;
}

Karel.instructions = {
   move: 1, turnLeft: 1, putBeeper: 1, pickBeeper: 1,
   turnRight: 2, turnAround: 2, paintCorner: 2,
};

Karel.predicates = {
   frontIsClear:1, frontIsBlocked:1,
   leftIsClear:1, leftIsBlocked:1,
   rightIsClear:1, rightIsBlocked:1,
   beepersPresent:1, noBeepersPresent:1,
   beepersInBag:1, noBeepersInBag:1,
   facingNorth:1, notFacingNorth:1,
   facingEast:1, notFacingEast:1,
   facingSouth:1, notFacingSouth:1,
   facingWest:1, notFacingWest:1,
   cornerColorIs:2, random:2
};

// Karel.translationDict = {
//   'move':'moverse',
//   'pickBeeper':'recogerCono',
//   'putBeeper':'ponerCono',

//   'turnLeft':'girarIzquierda',
//   'turnRight':'girarDerecha',
//   'turnAround':'mediaVeulta',

//   'paintCorner':'pintarEsquina',

//   'frontIsClear':'frenteDespejado',
//   'frontIsBlocked':'frenteBloqueado',

//   'leftIsClear':'izquierdaDespejada',
//   'leftIsBlocked':'izquierdaBloqueada',

//   'rightIsClear':'derechaDespejada',
//   'rightIsBlocked':'derechaBloqueada',

//   'beepersPresent':'conosPresentes',
//   'noBeepersPresent':'conosAusentes',

//   'beepersInBag':'bolsaConConos',
//   'noBeepersInBag':'bolsaSinConos',

//   'facingNorth':'rumboNorte',
//   'notFacingNorth':'sinRumboNorte',

//   'facingSouth':'rumboSur',
//   'notFacingSouth':'sinRumboSur',

//   'facingEast':'rumboEste',
//   'notFacingEast':'sinRumboEste',

//   'facingWest':'rumboOeste',
//   'notFacingWest':'sinRumboOeste',

//   'random':'aleatorio',

//   'cornerColorIs':'colorEsquinaEs'

// }
