
$(function() {
    var util = {
        renderTemplate: function($container, template, data) {
            data = (data instanceof Array) ? data : [ data ];
            $container.html("");
            function makeHtml(dict) {
                var html = template;
                $.each(dict, function(name, val) {
                    var pattern = new RegExp("{{" + name + "}}", "g");
                    html = html.replace(pattern, val);
                });
                return html;
            }
            for (var i = 0; i < data.length; i++) {
                var html = makeHtml(data[i]);
                $(html).appendTo($container);
            }
        },        
        calcDistance: function(p1, p2) {
            var sqrDist = 0;
            for (var i = 0; i < 3; i++) {
                sqrDist += p1[i] * p1[i] + p2[i] * p2[i];
            }
            return Math.sqrt(sqrDist);
        },
        fromBohrToAngs: function(unit) {
            return unit * 0.529;
        },
        roundNumber: function(number, digits) {
            var multiple = Math.pow(10, digits);
            var rndedNum = Math.round(number * multiple) / multiple;
            return rndedNum;
        }
    };

    var model = {
        steps: [
            [//step
                [ 1, 1, 1 ],//atom 1
                [ 2, 2, 2 ],//atom 2
            ] 
        ],
        atomPairs: [
           [ 0, 1 ]
        ],
        getMinDist: function() {
            return d3.min(this.distances);
        },
        getAverageDist: function() {
            return d3.mean(this.distances);
        },
        getMaxDist: function() {
            return d3.max(this.distances);
        },
        distances: [ 0, 0 ],
        setAtomPairs: function(selectedAtoms) {
            console.log("selected atoms:");
            console.log(JSON.stringify(selectedAtoms));
            this.atomPairs = [];
            console.log("atom pairs before:");
            console.log(JSON.stringify(this.atomPairs));
            for (var i = 0; i < selectedAtoms.length - 1; i++) {
                for (var j = i + 1; j < selectedAtoms.length; j++) {
                    var id0 = selectedAtoms[i];
                    var id1 = selectedAtoms[j];
                    this.atomPairs.push([ id0, id1 ]);
                }
            }
            console.log("atom pairs after:");
            console.log(JSON.stringify(this.atomPairs));
        },
        getAtomsCount: function() {
            var stepsCount = this.getStepsCount();
            return (stepsCount > 0) ? model.steps[0].length : 0;
        },
        getStepsCount: function() {
            return this.steps.length;
        },
        getAtomPairsCount: function() {
            return this.atomPairs.length;
        },
        getDataCount: function() {
            return this.getStepsCount() * this.getAtomPairsCount();
        },
        updateDistances: function() {
            this.distances = [];
            var pairs = this.atomPairs;
            var steps = this.steps;
            for (var i = 0; i < steps.length; i++) {
                var step = steps[i];
                for (var j = 0; j < pairs.length; j++) {
                    var pair = pairs[j];
                    var id0 = pair[0], id1 = pair[1];
                    var p0 = step[id0], p1 = step[id1];
                    var dist = util.calcDistance(p0, p1);
                    this.distances.push(util.fromBohrToAngs(dist));
                }
            }
        }
    };

    var controller = {
        init: function() {
            viewError.init();
            viewInfo.init();
            viewInfo.render({
                "atoms-count": 0,
                "steps-count": 0,
                "data-count": 0,
                "min-dist": 0,
                "average-dist": 0,
                "max-dist": 0
            });
            viewAtoms.init();
            viewLoading.init();
            viewGraph.init();
        },
        updateInfo: function() {
            try {
                var m = model;
                var info = {
                    "steps-count": m.getStepsCount(),
                    "atoms-count": m.getAtomsCount(),
                    "data-count": m.getDataCount(),
                    "min-dist": util.roundNumber(m.getMinDist(), 3),
                    "average-dist": util.roundNumber(m.getAverageDist(), 3),
                    "max-dist": util.roundNumber(m.getMaxDist(), 3)
                };
                viewInfo.render(info);
            } catch (e) {
                viewError.render("данные не верны: " + e.message);
            }
        },
        updateAtoms: function() {
            var m = model;
            var atomsData = [];
            for (var i = 1; i <= m.getAtomsCount(); i++) {
                atomsData.push({
                    "atom-id": i
                });
            }
            viewAtoms.render(atomsData);
        },
        updateGraph: function() {
            var binsCount = 26;
            var json = this.getGraphJson(binsCount);
            viewGraph.render(json);
        },
        processStepData: function(stepData) {
            var atomRe = /(-?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?)/gm;
            var rawAtomsCoords = stepData.match(atomRe);
            var atoms = [];
            for (var i = 0; i < rawAtomsCoords.length; i += 3) {
                var atom = [];
                for (var j = 0; j < 3; j++) {
                    var index = i + j;
                    var rawAtomCoord = rawAtomsCoords[index];
                    var atomCoord = parseFloat(rawAtomCoord);
                    atom.push(atomCoord);
                }
                atoms.push(atom);
            }
            return atoms;
        },
        processRawData: function(rawData) {
            viewLoading.render(rawData);
            var stepRe = /Cartesian coordinates \(xcart\) \[bohr\]((E|\s|\d|\.|-|\+)+)/gm;
            var rawStep;
            model.steps = [];
            while ((rawStep = stepRe.exec(rawData)) !== null) {
                var step = this.processStepData(rawStep[0]);
                model.steps.push(step);
            }
            if (model.steps.length === 0) {
                viewError.render("Не найдены данные молекулярной динамики. В файле не встречается 'Cartesian coordinates (xcart) [bohr]'");
                return;
            }
            this.updateInfo();
            this.updateAtoms();
        },
        setCheckedAtomsCount: function(count) {
            viewAtoms.setGraphButton(count > 1);
        },
        setAtomPairs: function(rawSelectedAtoms) {
            var selectedAtoms = [];
            for (var i = 0; i < rawSelectedAtoms.length; i++) {
                var rawAtomId = rawSelectedAtoms[i];
                var atomId = parseInt(rawAtomId.name) - 1;
                selectedAtoms.push(atomId);
            }
            model.setAtomPairs(selectedAtoms);
            model.updateDistances();
            console.log("atom pairs:");
            console.log(JSON.stringify(model.atomPairs));
            this.updateInfo();
            this.updateGraph();
        },
        getGraphJson: function(binsCount) {
            var distances = model.distances;
            var minVal = model.getMinDist();
            var maxVal = model.getMaxDist();
            console.log("max: " + maxVal);
            var step = (maxVal - minVal) / binsCount;
            var json = [];
            for (var i = 0; i < binsCount - 1; i++) {
                var begin = minVal + i * step;
                var end = begin + step;
                var bin = distances.filter(function(number) {
                    return begin <= number && number < end;
                });
                json.push({
                    "Number of Atoms": bin.length,
                    "Distance between Atoms [Angst]": util.roundNumber(end, 3)
                });
            }
            return json;
        }
    };

    var viewGraph = {
        init: function() {
            this.$graph = $('#graph');
        },
        render: function(json) {
            var $graph = this.$graph;
            $graph.html("");
            var svg = dimple.newSvg("#graph", $graph.width(), $graph.height());
            var myChart = new dimple.chart(svg, json);
            myChart.setBounds("10%", "2%", "85%", "80%");
            var x = myChart.addCategoryAxis("x", "Distance between Atoms [Angst]");
            //x.addOrderRule("Date");
            myChart.addMeasureAxis("y", "Number of Atoms");
            myChart.addSeries(null, dimple.plot.bar);
            myChart.draw();
        }
    };

    var viewLoading = {
        init: function() {
            this.$preview = $("#preview");
            $("#file-input").on('fileloaded', function(event, file, previewId, index, reader) {
                reader.onload = function(e) {
                    var rawData = e.target.result;
                    controller.processRawData(rawData);
                };
                reader.readAsText(file);
            });
        },
        render: function(rawData) {
            var limit = 80002;
            var preview = (rawData.length < limit) ? rawData : rawData.substr(0, limit - 2);
            this.$preview.text(preview);
        }
    };

    var viewError = {
        init: function() {
            this.$holder = $('#error-panel');
        },
        render: function(errorMessage) {
            this.$holder.text(errorMessage);
        }
    };

    var viewAtoms = {
        init: function() {
            this.$graphSubmit = $("#launch-graph");
            this.$atoms = $('#atoms');
            this.atomsTemplate = $('script[data-template="atoms"]').html();
            $('#atom-form').submit(function(event) {
                var rawSelectedAtoms = $(this).serializeArray();
                controller.setAtomPairs(rawSelectedAtoms);
                event.preventDefault();
            });
            $("#atom-form").on("click", "input[type = checkbox]", function() {
                var checkedCount = $("#atom-form input:checked").length;
                controller.setCheckedAtomsCount(checkedCount);
            });
        },
        setGraphButton: function(enabled) {
            this.$graphSubmit.prop("disabled", !enabled);
        },
        render: function(atoms) {
            util.renderTemplate(this.$atoms, this.atomsTemplate, atoms);
        }
    };

    var viewInfo = {
        init: function() {
            this.$info = $('#info');
            this.infoTemplate = $('script[data-template="info"]').html();

        },
        render: function(info) {
            util.renderTemplate(this.$info, this.infoTemplate, info);
        }
    };

    controller.init();
});
