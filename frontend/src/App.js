import React, {useEffect, useState} from 'react';
import axios from 'axios';

function App(){
  const [products,setProducts] = useState([]);
  useEffect(()=> {
    axios.get('/api/products').then(r=> setProducts(r.data));
  },[]);
  return (
    <div style={{maxWidth:900, margin:'0 auto', padding:20}}>
      <h1>Video Store (Demo)</h1>
      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:20}}>
        {products.map(p=> (
          <div key={p.id} style={{border:'1px solid #ddd', padding:10}}>
            <h3>{p.title}</h3>
            <p>{p.short_desc}</p>
            <video width="100%" controls>
              <source src={'/videos/' + p.filename} type="video/mp4" />
            </video>
            <p><strong>${p.price}</strong></p>
            <button onClick={async ()=> {
              // simple checkout flow using backend-created session
              const res = await axios.post('/api/create-checkout-session', {items:[{product_id:p.id, quantity:1}]});
              if(res.data.url) window.location = res.data.url;
            }}>Comprar</button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App;
