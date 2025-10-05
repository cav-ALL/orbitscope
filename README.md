# Orbitspace - Asteroid Impact Simulator

**Orbitspace** is a web-based, interactive simulator that allows users to model asteroid impact scenarios using real data from NASA. It's designed to be a simple and powerful educational tool to visualize and understand the potential consequences of a celestial impact.

---

## Basic Functionalities

### 1. **Search for Real Asteroids**
* The application connects directly to **NASA's Near-Earth Object (NEO) API**.
* Users can select a start date and a time range (up to 7 days) to fetch a list of actual asteroids that are passing near Earth during that period.

### 2. **Customize the Impact Scenario**
* **Select an Asteroid:** Choose a specific asteroid from the fetched list to simulate.
* **Adjust Parameters:** Use intuitive sliders to modify the **impact angle** and the **impact velocity** (in km/s).
* **Choose a Location:** An interactive 2D map (powered by Leaflet.js) allows you to drag and drop a marker to set the precise coordinates for the impact anywhere in the world.

### 3. **Run the Simulation & Analyze Results**
* With a click of a button, the application calculates the devastating consequences of the impact based on scientific formulas.
* The results are displayed in a clear and organized dashboard, including:
    * **Impact Energy** (in Exajoules and TNT equivalent)
    * **Crater Diameter** and Depth
    * **Earthquake Magnitude** on the Richter scale
    * **Estimated Casualties** and **Economic Impact**
    * An overall **Severity Level** (Local, Regional, or Planetary)

### 4. **Visualize the Devastation**
* The impact's effects are drawn directly on the 2D map.
* Two circles represent the **crater size** (in red) and the larger **affected area** (in orange), giving a clear visual sense of the scale of the destruction.

### 5. **Filter and Sort Threats**
* An integrated filter allows users to sort the list of asteroids by **impact energy** (high to low or low to high) or by **severity level**, making it easy to identify the most significant threats first.
