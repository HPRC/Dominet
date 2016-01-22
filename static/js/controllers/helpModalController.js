clientModule.controller("helpModalController", function($scope, $uibModalInstance) {
	$scope.close = function(){
		$uibModalInstance.dismiss("cancel");
	};

  //return element only if it is visible
  var isVisible = function(elem){
    if (elem.offsetWidth > 0 && elem.offsetHeight > 0){
      return elem;
    }
  }

  $scope.tourOptions = {
    steps:[
      {
        element: document.querySelector('#leftColumn'),
        intro: "This is the available supply, a set of cards available to buy from for all players"
      },
      {
        element: document.querySelector('.card-price'),
        intro: "The price a card costs to buy is on the left of each card",
        position: "bottom"
      },
      {
        element: document.querySelector('.supplyCardContainer button'),
        intro: "Hover over a card to see what it does.",
        position: "bottom"
      },
      {
        element: document.querySelector('.supplyCardContainer .badge'),
        intro: "The total number of cards available to get is displayed on the right",
        position: "bottom"
      },
      {
        element: document.querySelector('#hand'),
        intro: "These cards in the center represent your current hand",
        position: "bottom"
      },
      {
        element: isVisible(document.querySelector('#playerOptions')),
        intro: "Your current resources in play are listed above your hand during your turn",
        position: "bottom"
      },
      {
        element: isVisible(document.querySelector('#spendMoney')),
        intro: "The +$ button is a shortcut to play all Treasures in your hand with the exception of some treasures with special effects",
        position: "bottom"
      },
      {
        element: isVisible(document.querySelector('#rightColumn')),
        intro: "Your deck and discard counts are displayed here as well as the trash pile.",
        position: "bottom"
      },

    ],
    showStepNumbers: false,
    skipLabel: "Exit",
    exitOnEsc: true,
    tooltipClass: "tour-tooltip",
    tooltipButtonClass: "btn btn-default"
  }
});