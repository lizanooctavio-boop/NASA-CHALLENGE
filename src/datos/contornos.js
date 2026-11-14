/*
 * Contornos MUY simplificados (lon, lat), trazados a mano solo para orientar al lector.
 * No sirven para recortar datos ni para medir áreas. Cuando el JSON definitivo traiga
 * geometrías propias (campo opcional `contorno` en cada región), la demo las usa en su lugar.
 */
(function () {
  'use strict';
  // Frontera Honduras–Nicaragua, de oeste (golfo de Fonseca) a este (cabo Gracias a Dios)
  var fronteraHN = [[-87.3, 12.98], [-86.9, 13.25], [-86.75, 13.75], [-86.3, 13.77], [-86.0, 14.05],
    [-85.7, 14.1], [-85.15, 14.35], [-84.9, 14.8], [-84.5, 14.62], [-84.0, 14.75], [-83.6, 14.9], [-83.15, 15.0]];
  // Frontera Nicaragua–Costa Rica, de este (Caribe) a oeste (Pacífico)
  var fronteraNC = [[-83.65, 10.93], [-84.0, 10.92], [-84.35, 10.98], [-84.7, 11.08], [-85.1, 11.1],
    [-85.6, 11.2], [-85.7, 11.08]];

  var nicaragua = fronteraHN.concat([
    [-83.4, 14.4], [-83.3, 14.0], [-83.55, 13.6], [-83.5, 12.9], [-83.65, 12.4], [-83.7, 11.9],
    [-83.85, 11.4], [-83.65, 10.93]
  ]).concat(fronteraNC.slice(1)).concat([
    [-85.9, 11.3], [-86.25, 11.75], [-86.55, 12.1], [-86.85, 12.3], [-87.17, 12.48], [-87.65, 12.9], [-87.3, 12.98]
  ]);

  var honduras = fronteraHN.concat([
    [-83.75, 15.3], [-84.3, 15.8], [-85.0, 15.95], [-86.0, 15.95], [-86.9, 15.75], [-87.6, 15.85],
    [-88.2, 15.72], [-88.6, 15.35], [-88.95, 14.95], [-89.15, 14.6], [-89.35, 14.42], [-89.0, 14.2],
    [-88.5, 13.9], [-88.0, 13.9], [-87.75, 13.85], [-87.8, 13.4], [-87.4, 13.3], [-87.3, 12.98]
  ]);

  var costaRica = fronteraNC.concat([
    [-85.75, 10.8], [-85.85, 10.3], [-85.65, 9.9], [-85.1, 9.6], [-84.7, 9.6], [-84.6, 9.65],
    [-84.1, 9.4], [-83.7, 9.0], [-83.6, 8.45], [-83.3, 8.4], [-82.88, 8.03], [-82.93, 8.25],
    [-82.85, 8.65], [-82.9, 9.1], [-82.55, 9.55], [-83.0, 10.0], [-83.4, 10.55], [-83.65, 10.93]
  ]);

  var cocibolca = [[-85.95, 11.93], [-85.6, 12.1], [-85.35, 12.05], [-84.95, 11.85], [-84.85, 11.55],
    [-84.8, 11.2], [-85.05, 11.12], [-85.45, 11.3], [-85.75, 11.55], [-85.95, 11.93]];
  var xolotlan = [[-86.75, 12.35], [-86.45, 12.45], [-86.25, 12.3], [-86.45, 12.15], [-86.7, 12.2], [-86.75, 12.35]];

  window.SOF_CONTORNOS = {
    paises: { nicaragua: nicaragua, honduras: honduras, costa_rica: costaRica },
    lagos: [cocibolca, xolotlan],
    rotulos: { nicaragua: [-84.6, 13.95], honduras: [-87.2, 14.75], costa_rica: [-84.1, 9.95] }
  };
})();
