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
const SIMULATION_TICKS = 10000;

console.log('Loading graph data...');

// Load the vault data
const rawData = fs.readFileSync(INPUT_FILE, 'utf8');
const data = JSON.parse(rawData);

console.log(`Loaded ${data.nodes.length} nodes and ${data.links.length} links`);

// Auto-classify links to topic nodes as topic_link type
const topicNodeIds = new Set(data.nodes.filter(node => node.tags.includes("topic")).map(node => node.id));

data.links.forEach(link => {
    if (topicNodeIds.has(link.source) || topicNodeIds.has(link.target)) {
        link.type = "topic_link";
    }
});

console.log(`Auto-classified ${data.links.filter(l => l.type === "topic_link").length} topic links`);

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
const minSize = 16;
const maxSize = 32;
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
    .force("link", d3.forceLink(data.links)
        .id(d => d.id)
        .distance(d => d.type === "topic_link" ? 120 : 50)  // Topic links much longer
        .strength(d => d.type === "topic_link" ? 0.03 : 0.8)  // Make topic links very weak
    )
    .force("charge", d3.forceManyBody().strength(-275))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("x", d3.forceX(width / 2).strength(0.02))
    .force("y", d3.forceY(height / 2).strength(0.02))
    .force("collide", d3.forceCollide(d => d.size + 12).strength(1.0)) // Stronger collision with more padding
    .alpha(2.5)
    .alphaDecay(0.0002);

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
