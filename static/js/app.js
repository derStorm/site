(function() {
    var app = angular.module('App', ['angular-clipboard']);

    app.controller('CopyCtrl', ['$scope', function ($scope) {
        $scope.textToCopy = 'I can copy by clicking!';

        $scope.success = function () {
            console.log('Copied!');
        };

        $scope.fail = function (err) {
            console.error('Error!', err);
        }
    }]);

    app.directive('info', function () {
        return {
            restrict: 'AE',
            template: 'All pwok.pw URLs and click analytics are public and can be accessed by anyone'
        }
    });
}());
