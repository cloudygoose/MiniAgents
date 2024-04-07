# MiniAgents: A Visualization Interface for Simulacra

![](https://github.com/cloudygoose/MiniAgents/figs/title.jpg)

The MiniAgents visualization tool for simulacra.

Currently only Mac is supported. The project is still work-in-progress (like a 0.5 version), I'm releasing this version because it's already functional.

Disclaimer: So far there is no novelty related to NLP research in this project, it is a tool and not a paper. It is motivated by the "Generative Agents: Interactive Simulacra of Human Behavior" paper.

I'll be happy to answer questions.

Author: Tianxing He (https://cloudygoose.github.io/)

## Quick start

**Important: Please download this repo to the path ~/Documents/MiniAgents** . I'm sorry for the inconvenience, somehow it is hard for a unity-complied game to get its current path.

Download MiniAgent.app from the following shared google folder and put it in the repo folder (same folder as this README file, like ~/Documents/MiniAgents/MiniAgents_build.app). You may need to control-click it in the finder otherwise mac won't let you open it.

https://drive.google.com/drive/u/1/folders/1NR30Trp3TqmDPl_dTU7FN660KpR0U-Od

I have put the map files in ./ and 20 steps of random-simulation trajectory files in ./run0/ , so you should be able to directly run. Just click the app file open and click the "Go!" button in the game.

Tips:

1. You can change the step idx and number via the in-game buttons.
2. Press Esc to see the main menu, especially buttons for map editting.
3. If you want the admin to run faster, press shift.
4. To zoom in and out, use the scroll on your mouse.

## Run your own simulation

I give a minimal example of how simulation trajectories can be generated for this visualization interface.

The minimal setting only requires python3.11.

To generate another trajectory, go to minimal/ and run

> python backend.py --clear_dir

I put a lot of comments in backend.py to explain things. 

## Map editting

You can edit the sectors, areas, and items in the map. Press Esc to see the main menu, especially buttons for map editting.

Below, I show how to draw the grids (which is a rectangle) for a new sector.

![](https://github.com/cloudygoose/MiniAgents/figs/mapeditting.gif)

