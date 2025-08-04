#!/usr/bin/env node
/**
 * Precompute Graph Layout
 * Runs D3 force simulation and saves optimized node positions to JSON file
 */

import fs from 'fs';
import * as d3 from 'd3-force';

// Configuration
const INPUT_FILE = 'vault_data.json';
const OUTPUT_FILE = 'web/vault_data_with_positions.json';
const SIMULATION_TICKS = 5000;

console.log('Loading graph data...');

// Load the vault data
const rawData = fs.readFileSync(INPUT_FILE, 'utf8');
const data = JSON.parse(rawData);

console.log(`Loaded ${data.nodes.length} nodes and ${data.links.length} links`);

// Calculate node degrees (number of connections)
const nodeDegrees = {};
data.nodes.forEach(node => {
    nodeDegrees[node.id] = 0;
});

data.links.forEach(link => {
    nodeDegrees[link.source] = (nodeDegrees[link.source] || 0) + 1;
    nodeDegrees[link.target] = (nodeDegrees[link.target] || 0) + 1;
});

// Add size property based on degree
const minSize = 8;
const maxSize = 16;
const maxDegree = Math.max(...Object.values(nodeDegrees));
const minDegree = Math.min(...Object.values(nodeDegrees));

data.nodes.forEach(node => {
    const degree = nodeDegrees[node.id];
    // Scale size based on degree
    node.size = minSize + (maxSize - minSize) * ((degree - minDegree) / (maxDegree - minDegree));
});

console.log(`Node degrees range: ${minDegree} - ${maxDegree}`);

// Set up simulation dimensions (matching web app)
const width = 1200;
const height = 800;

console.log('Creating force simulation...');

// Create the same simulation as the web app
const simulation = d3.forceSimulation(data.nodes)
    .force("link", d3.forceLink(data.links).id(d => d.id).distance(50))
    .force("charge", d3.forceManyBody().strength(-200))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("x", d3.forceX(width / 2).strength(0.02))
    .force("y", d3.forceY(height / 2).strength(0.02))
    .alpha(1.2)
    .alphaDecay(0.0005);

console.log(`Running simulation for ${SIMULATION_TICKS} ticks...`);

// Stop automatic ticking and manually run simulation
simulation.stop();

// Run simulation manually for specified number of ticks
for (let i = 0; i < SIMULATION_TICKS; i++) {
    simulation.tick();
    
    // Progress indicator
    if (i % 50 === 0) {
        console.log(`  Tick ${i}/${SIMULATION_TICKS} (alpha: ${simulation.alpha().toFixed(4)})`);
    }
}

console.log('Simulation complete! Saving positions...');

// Create output data with computed positions
const outputData = {
    nodes: data.nodes.map(node => ({
        id: node.id,
        title: node.title,
        tags: node.tags,
        content: node.content,
        x: node.x,
        y: node.y,
        size: node.size
    })),
    links: data.links
};

// Write to output file
fs.writeFileSync(OUTPUT_FILE, JSON.stringify(outputData, null, 2));

console.log(`Saved optimized layout to ${OUTPUT_FILE}`);
console.log(`Final alpha: ${simulation.alpha().toFixed(6)}`);
console.log('Done!');
