clientModule.controller("appController", function($rootScope, $scope, client) {

  $scope.themeOptions = ['default', 'terminal'];
  $scope.theme = {
    selected: 'default'
  };

  $scope.resume = function(json){
    $scope.$apply(function(){
      $scope.main.game = true;
    });
  };

  $scope.$on("$destroy", function(){
    socketlistener();
  });

  var socketlistener = $rootScope.$on("socketmsg", function(data, event){
    var jsonres = JSON.parse(event.data);
    if (jsonres.command === "init"){
      client.onmessage(event);
    }
    var exec = $scope[jsonres.command];
    if (exec != undefined){
      exec.call($scope, jsonres);
    }
    $scope.$digest();
  });

});