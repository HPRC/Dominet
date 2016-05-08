var clientModule = angular.module(
  "clientApp", ['ui.bootstrap', 'angular-intro']
  ).config(['$compileProvider', function ($compileProvider) {
    $compileProvider.debugInfoEnabled(false);
  }]);
