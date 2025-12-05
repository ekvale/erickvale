# Quick Test Guide - 5 Minutes

## 🚀 Start Testing Now

### Step 1: Start the Server
The server should already be running. If not:
```bash
python manage.py runserver
```

### Step 2: Open the App
1. Open your browser
2. Go to: **http://127.0.0.1:8000/**
3. Click **"Launch App →"** on the Emergency Preparedness card

### Step 3: Generate PODs (30 seconds)
1. You'll see a map of Minnesota
2. In the left control panel, click **"Generate Optimal PODs"** button
3. Wait 2-3 seconds for the algorithm to run
4. PODs will appear on the map as numbered markers

### Step 4: View the Results (2 minutes)

**Click on any POD marker** to see:
- ✅ **Coverage Radius** - Notice it's NOT always 50km (dynamic!)
- ✅ **Vulnerable Population** - Shows vulnerable people covered
- ✅ **Infrastructure Score** - Quality of location (0-100%)
- ✅ **Estimated Capacity** - Daily capacity estimate
- ✅ **Capacity Utilization** - How well capacity is used
- ✅ **Redundancy Score** - Backup coverage percentage

**Check the Alert Message** after generation:
- Shows summary statistics
- Coverage percentage
- Uncovered population
- Critical gaps (if enabled)

**Look at the Sidebar (PODs tab)**:
- POD list shows new metrics
- Infrastructure scores visible
- Capacity information displayed

### Step 5: Compare Results (2 minutes)

**Test 1: Different Number of PODs**
- Change "Number of PODs" to 10
- Click "Generate Optimal PODs" again
- Compare coverage and placement

**Test 2: Check Dynamic Radius**
- Click on PODs in different areas:
  - Urban PODs (Minneapolis area) → Should have ~30km radius
  - Rural PODs → Should have ~70km radius

**Test 3: Test with Scenario**
1. Click "Add Scenario"
2. Create: Name="Test", Type="Pandemic", Severity=2.0
3. Select it from "Active Scenario" dropdown
4. Generate PODs again
5. Notice how placement changes for pandemic scenario

## 🎯 What You Should See

### ✅ Dynamic Radius
- **Urban PODs**: 25-40km radius (Minneapolis, St. Paul area)
- **Suburban PODs**: 40-60km radius
- **Rural PODs**: 60-80km radius

### ✅ Enhanced Metrics
Every POD should show:
- Infrastructure Score: 30-90% (higher in major cities)
- Estimated Capacity: 1,500-5,000 people/day
- Capacity Utilization: 50-90% (optimal range)
- Vulnerable Population: Number of vulnerable people covered

### ✅ Better Placement
- PODs should be in strategic locations
- High-risk areas should be prioritized
- Major cities should have better infrastructure scores
- Coverage should be more balanced

## 🔍 Quick Verification Checklist

- [ ] PODs appear on map after clicking "Generate Optimal PODs"
- [ ] POD popups show "Infrastructure Score"
- [ ] POD popups show "Estimated Capacity"
- [ ] POD popups show "Vulnerable Population"
- [ ] Coverage radius varies (not all 50km)
- [ ] Alert shows summary statistics
- [ ] Sidebar POD list shows new metrics

## 🐛 If Something Doesn't Work

1. **Check Browser Console** (F12 → Console tab)
   - Look for any red error messages
   
2. **Verify Server is Running**
   - Should see "Starting development server" message
   
3. **Check Network Tab** (F12 → Network tab)
   - Look for `/api/pods/optimal/` request
   - Should return 200 status

4. **Try Refreshing the Page**
   - Sometimes static files need refresh

## 📊 Expected Results for 5 PODs

- **Coverage**: 60-80% of Minnesota population
- **Average Infrastructure Score**: 50-70%
- **Average Drive Time**: 20-40 minutes
- **Radius Range**: 25-75km
- **Total Capacity**: 7,500-25,000 people/day

## 💡 Pro Tips

1. **Zoom in on PODs** to see coverage circles better
2. **Toggle "Show Coverage Areas"** to see/hide circles
3. **Toggle "Show Risk Points"** to see city risk levels
4. **Use "Analyze Scenario"** button after creating scenarios

That's it! You should now see all the enhanced optimization features in action.

