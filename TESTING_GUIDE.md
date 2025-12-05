# Testing Guide - POD Optimization Improvements

## Quick Start

### 1. Start the Django Server

```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

### 2. Access the Application

1. **Homepage**: Visit `http://127.0.0.1:8000/`
   - You'll see the Erickvale homepage with the Emergency Preparedness app

2. **Emergency Preparedness App**: Click "Launch App →" or visit `http://127.0.0.1:8000/apps/emergency/`
   - This opens the interactive map interface

## Testing the Enhanced Optimization

### Step-by-Step Testing

#### 1. Generate Optimal PODs (Basic Test)

1. In the Emergency Preparedness app, you'll see:
   - **Number of PODs** input (default: 5)
   - **Max Drive Time** input (default: 60 minutes)
   - **Generate Optimal PODs** button

2. Click **"Generate Optimal PODs"**
   - The algorithm will run with all the new enhancements
   - PODs will appear on the map with numbered markers
   - Coverage circles will show the dynamic radius for each POD

3. **Check the Results**:
   - Click on any POD marker to see detailed information including:
     - Coverage radius (now dynamic, not fixed 50km)
     - Vulnerable population covered
     - Infrastructure score
     - Estimated capacity
     - Capacity utilization
     - Redundancy score

#### 2. View Enhanced Metrics

**In the POD Popup** (click any POD marker):
- Look for new fields:
  - `Vulnerable Population`: Shows vulnerable people covered
  - `Infrastructure Score`: Quality of location (0-100%)
  - `Estimated Capacity`: Daily capacity estimate
  - `Capacity Utilization`: How well capacity is used
  - `Redundancy Score`: Backup coverage percentage

**In the Sidebar** (PODs tab):
- POD list items now show:
  - Vulnerable population
  - Infrastructure score
  - Capacity information

#### 3. Test Different Scenarios

1. **Create a Scenario**:
   - Click "Add Scenario" button
   - Fill in:
     - Name: "Test Pandemic"
     - Type: "Pandemic"
     - Severity: 2.0
   - Save

2. **Select Active Scenario**:
   - Use the "Active Scenario" dropdown
   - Select your scenario

3. **Generate PODs with Scenario**:
   - Click "Generate Optimal PODs"
   - The algorithm will use scenario-specific risk modifications
   - Results will reflect pandemic-specific priorities

#### 4. Test Coverage Gap Analysis

The gap analysis is automatically included when you generate PODs. Check the alert message after generation - it will show:
- Coverage percentage
- Uncovered population
- Number of critical gaps

#### 5. Test Different Parameters

Try different combinations:

**Test 1: More PODs**
- Set Number of PODs to 10
- Generate and compare coverage

**Test 2: Stricter Drive Time**
- Set Max Drive Time to 30 minutes
- See how POD placement changes

**Test 3: Different Scenarios**
- Create scenarios with different types (Natural Disaster, Severe Weather)
- Compare POD placements

## API Testing (Advanced)

### Using Browser Console

Open browser DevTools (F12) and try:

```javascript
// Test optimal POD generation with all features
fetch('/apps/emergency/api/pods/optimal/?num_pods=5&max_drive_time=60&analyze_gaps=true')
  .then(r => r.json())
  .then(data => {
    console.log('Summary:', data.summary);
    console.log('Gap Analysis:', data.gap_analysis);
    console.log('PODs:', data.pods);
  });
```

### Using curl (Command Line)

```bash
# Generate 5 PODs with gap analysis
curl "http://127.0.0.1:8000/apps/emergency/api/pods/optimal/?num_pods=5&max_drive_time=60&analyze_gaps=true"
```

## What to Look For

### ✅ Dynamic Radius
- Urban PODs (Minneapolis, St. Paul) should have smaller radii (~30km)
- Rural PODs should have larger radii (~70km)
- Check the "Coverage Radius" in POD popups

### ✅ Capacity Constraints
- PODs should have estimated capacity values
- Capacity utilization should be reasonable (not over 100%)
- Large cities should have higher capacity estimates

### ✅ Infrastructure Scores
- Major cities should have higher infrastructure scores (70-90%)
- Small towns should have lower scores (30-50%)
- Check proximity to Minneapolis/St. Paul affects scores

### ✅ Vulnerable Population
- PODs should show vulnerable population covered
- Smaller cities should have higher vulnerability scores

### ✅ Redundancy
- High-risk areas should have some redundancy (overlap)
- Redundancy scores should be > 0 for critical areas

### ✅ Multi-Objective Optimization
- PODs should balance multiple factors, not just population
- Check that high-risk areas are prioritized
- Verify accessibility (drive times) are reasonable

## Troubleshooting

### If PODs don't appear:
1. Check browser console for errors (F12)
2. Verify the server is running
3. Check that demographic_data.json exists

### If metrics are missing:
- Some metrics only appear for newly generated PODs
- Try generating new PODs to see all features

### If optimization seems slow:
- The enhanced algorithm is more complex
- For 5 PODs, it should complete in 1-3 seconds
- For 20 PODs, it may take 5-10 seconds

## Expected Results

After generating 5 PODs for Minnesota:
- **Coverage**: Should cover 60-80% of population
- **Infrastructure**: Average score should be 50-70%
- **Drive Times**: Average should be 20-40 minutes
- **Radius Range**: 25-75km depending on location
- **Capacity**: Each POD should handle 1,500-5,000 people/day

## Next Steps

1. **Compare Old vs New**: Generate PODs and note the differences
2. **Test Edge Cases**: Try extreme values (1 POD, 20 PODs, 10 min drive time)
3. **Scenario Testing**: Create different scenarios and compare results
4. **Gap Analysis**: Use gap analysis to identify where more PODs are needed



